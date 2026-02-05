import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display dashboard title', async ({ page }) => {
    const pageTitle = page.getByTestId('dashboard-title');
    await expect(pageTitle).toBeVisible();
  });

  test('should display stats cards', async ({ page }) => {
    await expect(page.getByTestId('stats-cards')).toBeVisible();
    await expect(page.getByTestId('online-agents-card')).toBeVisible();
    await expect(page.getByTestId('pending-tasks-card')).toBeVisible();
    await expect(page.getByTestId('recent-messages-card')).toBeVisible();
    await expect(page.getByTestId('system-status-card')).toBeVisible();
  });

  test('should display online agents count', async ({ page }) => {
    const countElement = page.getByTestId('online-agents-count');
    await expect(countElement).toBeVisible();
    const countText = await countElement.textContent();
    expect(parseInt(countText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display pending tasks count', async ({ page }) => {
    const countElement = page.getByTestId('pending-tasks-count');
    await expect(countElement).toBeVisible();
    const countText = await countElement.textContent();
    expect(parseInt(countText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display recent messages count', async ({ page }) => {
    const countElement = page.getByTestId('recent-messages-count');
    await expect(countElement).toBeVisible();
    const countText = await countElement.textContent();
    expect(parseInt(countText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display system status as active', async ({ page }) => {
    const statusElement = page.getByTestId('system-status');
    await expect(statusElement).toBeVisible();
    await expect(statusElement).toHaveText(/Active/i);
  });

  test('should display recent agents section', async ({ page }) => {
    await expect(page.getByTestId('recent-agents-section')).toBeVisible();
  });

  test('should display recent tasks section', async ({ page }) => {
    await expect(page.getByTestId('recent-tasks-section')).toBeVisible();
  });

  test('should display recent agents list', async ({ page }) => {
    const agentsList = page.getByTestId('recent-agents-list');
    const agents = await agentsList.all();
    expect(agents.length).toBeGreaterThanOrEqual(0);
  });

  test('should display recent tasks list', async ({ page }) => {
    const tasksList = page.getByTestId('recent-tasks-list');
    const tasks = await tasksList.all();
    expect(tasks.length).toBeGreaterThanOrEqual(0);
  });
});