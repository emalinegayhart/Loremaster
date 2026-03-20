package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
	"time"
)

const (
	BaseURL      = "https://wowpedia.fandom.com/api.php"
	UserAgent    = "WowpediaScraper/1.0 (educational project)"
	RequestDelay = 750 * time.Millisecond
	BatchSize    = 50
)

type CategoryMembersResponse struct {
	Query struct {
		CategoryMembers []CategoryMember `json:"categorymembers"`
	} `json:"query"`
	Continue *struct {
		CMContinue string `json:"cmcontinue"`
		Continue   string `json:"continue"`
	} `json:"continue"`
}

type CategoryMember struct {
	PageID int    `json:"pageid"`
	NS     int    `json:"ns"`
	Title  string `json:"title"`
}

type PagesResponse struct {
	Query struct {
		Pages map[string]PageResult `json:"pages"`
	} `json:"query"`
}

type PageResult struct {
	PageID     int    `json:"pageid"`
	NS         int    `json:"ns"`
	Title      string `json:"title"`
	Missing    string `json:"missing"`
	Redirect   string `json:"redirect"`
	Touched    string `json:"touched"`
	Categories []struct {
		Title string `json:"title"`
	} `json:"categories"`
	Links []struct {
		NS    int    `json:"ns"`
		Title string `json:"title"`
	} `json:"links"`
	Revisions []struct {
		Timestamp string `json:"timestamp"`
		Slots     struct {
			Main struct {
				Content string `json:"*"`
			} `json:"main"`
		} `json:"slots"`
	} `json:"revisions"`
}

type APIClient struct {
	http          *http.Client
	lastRequestAt time.Time
}

func NewAPIClient() *APIClient {
	return &APIClient{
		http: &http.Client{Timeout: 30 * time.Second},
	}
}

func (c *APIClient) get(params map[string]string) ([]byte, error) {
	if wait := RequestDelay - time.Since(c.lastRequestAt); wait > 0 {
		time.Sleep(wait)
	}
	c.lastRequestAt = time.Now()

	q := url.Values{}
	q.Set("format", "json")
	q.Set("maxlag", "5")
	for k, v := range params {
		q.Set(k, v)
	}

	reqURL := fmt.Sprintf("%s?%s", BaseURL, q.Encode())
	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", UserAgent)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == 429 {
		retryAfter := resp.Header.Get("Retry-After")
		log.Printf("Rate limited by server, Retry-After: %s", retryAfter)
		time.Sleep(15 * time.Second)
		return c.get(params)
	}

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("unexpected status: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read body: %w", err)
	}

	var apiErr struct {
		Error *struct {
			Code string `json:"code"`
			Info string `json:"info"`
		} `json:"error"`
	}
	if err := json.Unmarshal(body, &apiErr); err == nil && apiErr.Error != nil {
		if apiErr.Error.Code == "maxlag" {
			log.Printf("Server maxlag, backing off 10s...")
			time.Sleep(10 * time.Second)
			return c.get(params)
		}
		return nil, fmt.Errorf("API error [%s]: %s", apiErr.Error.Code, apiErr.Error.Info)
	}

	return body, nil
}

func (c *APIClient) GetCategoryMembers(categoryTitle string) ([]CategoryMember, error) {
	var allMembers []CategoryMember
	continueToken := ""

	for {
		params := map[string]string{
			"action":  "query",
			"list":    "categorymembers",
			"cmtitle": categoryTitle,
			"cmlimit": "500",
			"cmtype":  "page|subcat",
		}
		if continueToken != "" {
			params["cmcontinue"] = continueToken
		}

		body, err := c.get(params)
		if err != nil {
			return nil, fmt.Errorf("GetCategoryMembers(%s): %w", categoryTitle, err)
		}

		var result CategoryMembersResponse
		if err := json.Unmarshal(body, &result); err != nil {
			return nil, fmt.Errorf("failed to parse category response: %w", err)
		}

		allMembers = append(allMembers, result.Query.CategoryMembers...)

		if result.Continue == nil {
			break
		}
		continueToken = result.Continue.CMContinue
	}

	return allMembers, nil
}

func (c *APIClient) GetPages(titles []string) (map[string]PageResult, error) {
	if len(titles) == 0 {
		return nil, nil
	}
	if len(titles) > BatchSize {
		return nil, fmt.Errorf("too many titles: max %d, got %d", BatchSize, len(titles))
	}

	body, err := c.get(map[string]string{
		"action":    "query",
		"titles":    strings.Join(titles, "|"),
		"prop":      "revisions|categories|links|info",
		"rvprop":    "content|timestamp",
		"rvslots":   "main",
		"cllimit":   "100",
		"pllimit":   "100",
		"inprop":    "url",
		"redirects": "1",
	})
	if err != nil {
		return nil, fmt.Errorf("GetPages: %w", err)
	}

	var result PagesResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse pages response: %w", err)
	}

	return result.Query.Pages, nil
}
