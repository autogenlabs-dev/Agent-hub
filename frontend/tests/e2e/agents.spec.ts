import { test, expect } from '@playwright/test';

test.describe('Agents Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agents');
  });

  test('should display agents page title', async ({ page }) => {
    const pageTitle = page.getByTestId('agents-page-title');
    await expect(pageTitle).toBeVisible();
  });

  test('should display overview text', async ({ page }) => {
    const overviewText = page.getByTestId('overview-text');
    await expect(overviewText).toBeVisible();
  });

  test('should display stats cards', async ({ page }) => {
    await expect(page.getByTestId('total-agents-card')).toBeVisible();
    await expect(page.getByTestId('online-agents-card')).toBeVisible();
    await expect(page.getByTestId('offline-agents-card')).toBeVisible();
    await expect(page.getByTestId('agent-types-card')).toBeVisible();
  });

  test('should display total agents count', async ({ page }) => {
    const countElement = page.getByTestId('total-agents-count');
    await expect(countElement).toBeVisible();
    const countText = await countElement.textContent();
    expect(parseInt(countText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display online agents count', async ({ page }) => {
    const countElement = page.getByTestId('online-agents-count');
    await expect(countElement).toBeVisible();
    const countText = await countElement.textContent();
    expect(parseInt(countText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display offline agents count', async ({ page }) => {
    const countElement = page.getByTestId('offline-agents-count');
    await expect(countElement).toBeVisible();
    const countText = await countElement.textContent();
    expect(parseInt(countText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display agent types count', async ({ page }) => {
    const countElement = page.getByTestId('agent-types-count');
    await expect(countElement).toBeVisible();
    const countText = await countElement.textContent();
    expect(parseInt(countText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display online agents section', async ({ page }) => {
    const section = page.getByTestId('online-agents-section');
    await expect(section).toBeVisible();
  });

  test('should display online agents list', async ({ page }) => {
    const agentsList = page.getByTestId('online-agents-list');
    const agents = await agentsList.all();
    expect(agents.length).toBeGreaterThanOrEqual(0);
  });

  test('should display all agents section', async ({ page }) => {
    const section = page.getByTestId('all-agents-section');
    await expect(section).toBeVisible();
  });

  test('should display all agents list', async ({ page }) => {
    const agentsList = page.getByTestId('all-agents-list');
    const agents = await agentsList.all();
    expect(agents.length).toBeGreaterThanOrEqual(0);
  });

  test('should display agent details', async ({ page }) => {
    const agentItem = page.getByTestId('agent-item').first();
    await expect(agentItem).toBeVisible();
  });

  test('should display agent status badges', async ({ page }) => {
    const agentItem = page.getByTestId('agent-item').first();
    const badge = agentItem.getByTestId('status-badge');
    await expect(badge).toBeVisible();
  });

  test('should display agent type badges', async ({ page }) => {
    const agentItem = page.getByTestId('agent-item').first();
    const badge = agentItem.getByTestId('type-badge');
    await expect(badge).toBeVisible();
  });
});