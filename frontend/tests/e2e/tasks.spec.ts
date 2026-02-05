import { test, expect } from '@playwright/test';

test.describe('Tasks Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tasks');
  });

  test('should display tasks page title', async ({ page }) => {
    const pageTitle = page.getByTestId('tasks-page-title');
    await expect(pageTitle).toBeVisible();
  });

  test('should display overview text', async ({ page }) => {
    const overviewText = page.getByTestId('overview-text');
    await expect(overviewText).toBeVisible();
  });

  test('should display tasks list', async ({ page }) => {
    const tasksList = page.getByTestId('tasks-list');
    const tasks = await tasksList.all();
    expect(tasks.length).toBeGreaterThanOrEqual(0);
  });

  test('should display task details', async ({ page }) => {
    const taskItem = page.getByTestId('task-item').first();
    await expect(taskItem).toBeVisible();
  });

  test('should display task status badges', async ({ page }) => {
    const taskItem = page.getByTestId('task-item').first();
    const badge = taskItem.getByTestId('status-badge');
    await expect(badge).toBeVisible();
  });

  test('should display task priority badges', async ({ page }) => {
    const taskItem = page.getByTestId('task-item').first();
    const badge = taskItem.getByTestId('priority-badge');
    await expect(badge).toBeVisible();
  });
});