import { test, expect } from '@playwright/test';

test.describe('Dashboard E2E Tests', () => {
  test('should navigate to dashboard', async ({ page }) => {
    await page.goto('http://localhost:5173/');
    await expect(page).toHaveURL(/.*localhost:5173/);
  });

  test('should display dashboard title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();
    await expect(page.getByText(/Overview of your agent communication channel/i)).toBeVisible();
  });

  test('should display online agents card', async ({ page }) => {
    await expect(page.getByRole('region', { name: /Online Agents/i })).toBeVisible();
  });

  test('should display pending tasks card', async ({ page }) => {
    await expect(page.getByRole('region', { name: /Pending Tasks/i })).toBeVisible();
  });

  test('should display recent messages card', async ({ page }) => {
    await expect(page.getByRole('region', { name: /Recent Messages/i })).toBeVisible();
  });

  test('should display system status card', async ({ page }) => {
    await expect(page.getByRole('region', { name: /System Status/i })).toBeVisible();
  });

  test('should display recent agents section', async ({ page }) => {
    await expect(page.getByRole('region', { name: /Recent Agents/i })).toBeVisible();
  });

  test('should display recent tasks section', async ({ page }) => {
    await expect(page.getByRole('region', { name: /Recent Tasks/i })).toBeVisible();
  });

  test('should navigate to agents page', async ({ page }) => {
    await page.getByRole('link', { name: /agents/i }).click();
    await expect(page).toHaveURL(/.*agents/);
  });

  test('should navigate to tasks page', async ({ page }) => {
    await page.getByRole('link', { name: /tasks/i }).click();
    await expect(page).toHaveURL(/.*tasks/);
  });

  test('should navigate to messages page', async ({ page }) => {
    await page.getByRole('link', { name: /messages/i }).click();
    await expect(page).toHaveURL(/.*messages/);
  });
});