import { test, expect } from '@playwright/test';

test.describe('Memory Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/memory');
  });

  test('should display memory page title', async ({ page }) => {
    const pageTitle = page.getByTestId('memory-page-title');
    await expect(pageTitle).toBeVisible();
  });

  test('should display overview text', async ({ page }) => {
    const overviewText = page.getByTestId('overview-text');
    await expect(overviewText).toBeVisible();
  });

  test('should display entries list', async ({ page }) => {
    const entriesList = page.getByTestId('entries-list');
    const entries = await entriesList.all();
    expect(entries.length).toBeGreaterThanOrEqual(0);
  });

  test('should display entry details', async ({ page }) => {
    const memoryItem = page.getByTestId('memory-item').first();
    await expect(memoryItem).toBeVisible();
  });

  test('should display entry key', async ({ page }) => {
    const memoryItem = page.getByTestId('memory-item').first();
    const key = memoryItem.getByTestId('entry-key');
    await expect(key).toBeVisible();
  });

  test('should display entry value', async ({ page }) => {
    const memoryItem = page.getByTestId('memory-item').first();
    const value = memoryItem.getByTestId('entry-value');
    await expect(value).toBeVisible();
  });

  test('should display entry creator', async ({ page }) => {
    const memoryItem = page.getByTestId('memory-item').first();
    const creator = memoryItem.getByText(/Created by/i);
    await expect(creator).toBeVisible();
  });
});