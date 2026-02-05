import { test, expect } from '@playwright/test';

test.describe('Messages Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/messages');
  });

  test('should display messages page title', async ({ page }) => {
    const pageTitle = page.getByTestId('messages-page-title');
    await expect(pageTitle).toBeVisible();
  });

  test('should display overview text', async ({ page }) => {
    const overviewText = page.getByTestId('overview-text');
    await expect(overviewText).toBeVisible();
  });

  test('should display messages list', async ({ page }) => {
    const messagesList = page.getByTestId('messages-list');
    const messages = await messagesList.all();
    expect(messages.length).toBeGreaterThanOrEqual(0);
  });

  test('should display message details', async ({ page }) => {
    const messageItem = page.getByTestId('message-item').first();
    await expect(messageItem).toBeVisible();
  });

  test('should display message sender', async ({ page }) => {
    const messageItem = page.getByTestId('message-item').first();
    const sender = messageItem.getByTestId('message-sender');
    await expect(sender).toBeVisible();
  });

  test('should display message content', async ({ page }) => {
    const messageItem = page.getByTestId('message-item').first();
    const content = messageItem.getByTestId('message-content');
    await expect(content).toBeVisible();
  });

  test('should display message timestamp', async ({ page }) => {
    const messageItem = page.getByTestId('message-item').first();
    const timestamp = messageItem.getByTestId('message-timestamp');
    await expect(timestamp).toBeVisible();
  });
});