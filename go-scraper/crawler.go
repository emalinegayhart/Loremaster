package main

import (
	"encoding/json"
	"io"
	"log"
	"strings"
	"time"
)

type RawPage struct {
	PageID       int      `json:"page_id"`
	Title        string   `json:"title"`
	Namespace    int      `json:"namespace"`
	URL          string   `json:"url"`
	Wikitext     string   `json:"wikitext"`
	Categories   []string `json:"categories"`
	Links        []string `json:"links"`
	LastModified string   `json:"last_modified"`
	IsRedirect   bool     `json:"is_redirect"`
	ScrapedAt    string   `json:"scraped_at"`
}

type Crawler struct {
	client     *APIClient
	checkpoint *Checkpoint
	output     io.Writer
	queue      []string
}

func NewCrawler(client *APIClient, checkpoint *Checkpoint, output io.Writer) *Crawler {
	return &Crawler{
		client:     client,
		checkpoint: checkpoint,
		output:     output,
	}
}

func (c *Crawler) CrawlCategory(categoryTitle string) error {
	if c.checkpoint.HasCategory(categoryTitle) {
		log.Printf("Skipping already-crawled category: %s", categoryTitle)
		return nil
	}

	log.Printf("Fetching members of: %s", categoryTitle)

	members, err := c.client.GetCategoryMembers(categoryTitle)
	if err != nil {
		return err
	}

	log.Printf("  Found %d members in %s", len(members), categoryTitle)

	for _, member := range members {
		switch member.NS {
		case 14:
			if err := c.CrawlCategory(member.Title); err != nil {
				log.Printf("  Error crawling subcategory %s: %v", member.Title, err)
			}
		case 0:
			if !c.checkpoint.HasPage(member.PageID) {
				c.queue = append(c.queue, member.Title)
			}
		}

		if len(c.queue) >= BatchSize {
			if err := c.flushQueue(); err != nil {
				log.Printf("  Error flushing queue: %v", err)
			}
		}
	}

	c.checkpoint.AddCategory(categoryTitle)
	c.checkpoint.Save()

	return nil
}

func (c *Crawler) flushQueue() error {
	if len(c.queue) == 0 {
		return nil
	}

	batch := c.queue[:BatchSize]
	if len(c.queue) < BatchSize {
		batch = c.queue
	}
	c.queue = c.queue[len(batch):]

	log.Printf("Fetching batch of %d pages...", len(batch))

	pages, err := c.client.GetPages(batch)
	if err != nil {
		return err
	}

	written := 0
	for _, page := range pages {
		if page.PageID <= 0 {
			continue
		}
		if c.checkpoint.HasPage(page.PageID) {
			continue
		}

		raw := c.buildRawPage(page)
		if err := c.writePage(raw); err != nil {
			log.Printf("  Failed to write page %d (%s): %v", page.PageID, page.Title, err)
			continue
		}

		c.checkpoint.AddPage(page.PageID)
		written++
	}

	log.Printf("  Wrote %d pages (total: %d)", written, c.checkpoint.PageCount())
	return nil
}

func (c *Crawler) FlushRemaining() error {
	for len(c.queue) > 0 {
		if err := c.flushQueue(); err != nil {
			return err
		}
	}
	return nil
}

func (c *Crawler) buildRawPage(p PageResult) RawPage {
	wikitext := ""
	lastModified := ""
	if len(p.Revisions) > 0 {
		wikitext = p.Revisions[0].Slots.Main.Content
		lastModified = p.Revisions[0].Timestamp
	}

	categories := make([]string, 0, len(p.Categories))
	for _, cat := range p.Categories {
		name := strings.TrimPrefix(cat.Title, "Category:")
		categories = append(categories, name)
	}

	links := make([]string, 0, len(p.Links))
	for _, link := range p.Links {
		if link.NS == 0 {
			links = append(links, link.Title)
		}
	}

	return RawPage{
		PageID:       p.PageID,
		Title:        p.Title,
		Namespace:    p.NS,
		URL:          buildURL(p.Title),
		Wikitext:     wikitext,
		Categories:   categories,
		Links:        links,
		LastModified: lastModified,
		IsRedirect:   p.Redirect != "",
		ScrapedAt:    time.Now().UTC().Format(time.RFC3339),
	}
}

func (c *Crawler) writePage(page RawPage) error {
	data, err := json.Marshal(page)
	if err != nil {
		return err
	}
	_, err = c.output.Write(append(data, '\n'))
	return err
}

func buildURL(title string) string {
	slug := strings.ReplaceAll(title, " ", "_")
	return "https://wowpedia.fandom.com/wiki/" + slug
}
