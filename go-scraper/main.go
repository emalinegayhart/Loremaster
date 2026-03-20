package main

import (
	"flag"
	"log"
	"os"
	"path/filepath"
	"strings"
)

var defaultCategories = []string{
	"Category:Characters",
	"Category:Quests",
	"Category:Items",
	"Category:Spells",
	"Category:Zones",
	"Category:NPCs",
	"Category:Lore",
}

func main() {
	outputDir := flag.String("output", "../data/raw", "Directory to write JSONL output files")
	checkpointPath := flag.String("checkpoint", "checkpoint.json", "File to save/load scrape progress")
	categoriesFlag := flag.String("categories", "", "Comma-separated list of categories to crawl (overrides defaults)")
	flag.Parse()

	if err := os.MkdirAll(*outputDir, 0755); err != nil {
		log.Fatalf("Failed to create output directory: %v", err)
	}

	categories := defaultCategories
	if *categoriesFlag != "" {
		categories = strings.Split(*categoriesFlag, ",")
	}

	checkpoint := LoadCheckpoint(*checkpointPath)

	outPath := filepath.Join(*outputDir, "pages.jsonl")
	outFile, err := os.OpenFile(outPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatalf("Failed to open output file: %v", err)
	}
	defer outFile.Close()

	log.Printf("Output → %s", outPath)
	log.Printf("Checkpoint → %s", *checkpointPath)
	log.Printf("Crawling %d seed categories...", len(categories))

	client := NewAPIClient()
	crawler := NewCrawler(client, checkpoint, outFile)

	for _, cat := range categories {
		cat = strings.TrimSpace(cat)
		log.Printf("━━━ Starting category: %s ━━━", cat)
		if err := crawler.CrawlCategory(cat); err != nil {
			log.Printf("Error crawling %s: %v", cat, err)
		}
	}

	if err := crawler.FlushRemaining(); err != nil {
		log.Printf("Error flushing remaining pages: %v", err)
	}

	checkpoint.Save()
	log.Printf("━━━ Done. Total pages scraped: %d ━━━", checkpoint.PageCount())
	log.Printf("Raw data saved to: %s", outPath)
}
