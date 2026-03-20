package main

import (
	"encoding/json"
	"log"
	"os"
	"sync"
)

type Checkpoint struct {
	mu                sync.Mutex
	ScrapedPageIDs    map[int]bool    `json:"scraped_page_ids"`
	CrawledCategories map[string]bool `json:"crawled_categories"`
	filePath          string
}

func NewCheckpoint() *Checkpoint {
	return &Checkpoint{
		ScrapedPageIDs:    make(map[int]bool),
		CrawledCategories: make(map[string]bool),
	}
}

func LoadCheckpoint(filePath string) *Checkpoint {
	cp := NewCheckpoint()
	cp.filePath = filePath

	data, err := os.ReadFile(filePath)
	if os.IsNotExist(err) {
		log.Printf("No checkpoint file found at %s, starting fresh", filePath)
		return cp
	}
	if err != nil {
		log.Printf("Warning: could not read checkpoint file: %v — starting fresh", err)
		return cp
	}

	if err := json.Unmarshal(data, cp); err != nil {
		log.Printf("Warning: could not parse checkpoint file: %v — starting fresh", err)
		return cp
	}

	log.Printf("Loaded checkpoint: %d pages scraped, %d categories crawled",
		len(cp.ScrapedPageIDs), len(cp.CrawledCategories))
	return cp
}

func (cp *Checkpoint) Save() {
	cp.mu.Lock()
	defer cp.mu.Unlock()

	data, err := json.MarshalIndent(cp, "", "  ")
	if err != nil {
		log.Printf("Warning: failed to marshal checkpoint: %v", err)
		return
	}
	if err := os.WriteFile(cp.filePath, data, 0644); err != nil {
		log.Printf("Warning: failed to save checkpoint: %v", err)
	}
}

func (cp *Checkpoint) HasPage(pageID int) bool {
	cp.mu.Lock()
	defer cp.mu.Unlock()
	return cp.ScrapedPageIDs[pageID]
}

func (cp *Checkpoint) AddPage(pageID int) {
	cp.mu.Lock()
	defer cp.mu.Unlock()
	cp.ScrapedPageIDs[pageID] = true
}

func (cp *Checkpoint) HasCategory(title string) bool {
	cp.mu.Lock()
	defer cp.mu.Unlock()
	return cp.CrawledCategories[title]
}

func (cp *Checkpoint) AddCategory(title string) {
	cp.mu.Lock()
	defer cp.mu.Unlock()
	cp.CrawledCategories[title] = true
}

func (cp *Checkpoint) PageCount() int {
	cp.mu.Lock()
	defer cp.mu.Unlock()
	return len(cp.ScrapedPageIDs)
}
