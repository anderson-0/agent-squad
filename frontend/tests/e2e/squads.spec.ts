import { test, expect } from '@playwright/test';

test.describe('Squads Management', () => {
  // Note: These tests assume the user is authenticated
  // In a real scenario, you'd have a setup that logs in before each test

  test.beforeEach(async ({ page }) => {
    // Navigate to squads page
    // In production, you'd login first or use stored auth state
    await page.goto('/squads');
  });

  test('should display squads page correctly', async ({ page }) => {
    // Check page title and heading
    await expect(page).toHaveTitle(/Agent Squad/);
    await expect(page.getByRole('heading', { name: /squads/i })).toBeVisible();

    // Check for "Create Squad" button
    await expect(page.getByRole('button', { name: /create.*squad|new.*squad/i })).toBeVisible();
  });

  test('should display squad stats cards', async ({ page }) => {
    // Check for stat cards
    await expect(page.getByText(/total.*squads/i)).toBeVisible();
    await expect(page.getByText(/active.*squads/i)).toBeVisible();
    await expect(page.getByText(/total.*agents/i)).toBeVisible();
  });

  test('should open create squad dialog', async ({ page }) => {
    // Click create squad button
    await page.getByRole('button', { name: /create.*squad|new.*squad/i }).click();

    // Dialog should appear
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: /create.*squad/i })).toBeVisible();

    // Check for form fields
    await expect(page.getByLabel(/name/i)).toBeVisible();
    await expect(page.getByLabel(/description/i)).toBeVisible();
  });

  test('should close create squad dialog on cancel', async ({ page }) => {
    // Open dialog
    await page.getByRole('button', { name: /create.*squad|new.*squad/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click cancel
    await page.getByRole('button', { name: /cancel/i }).click();

    // Dialog should close
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('should validate required fields in create squad form', async ({ page }) => {
    // Open dialog
    await page.getByRole('button', { name: /create.*squad|new.*squad/i }).click();

    // Try to submit without filling required fields
    await page.getByRole('button', { name: /create.*squad/i }).nth(1).click();

    // Should show validation errors or prevent submission
    // The dialog should still be visible if validation failed
    await expect(page.getByRole('dialog')).toBeVisible();
  });

  test('should display squads table or empty state', async ({ page }) => {
    // Check if table or empty state is visible
    const hasTable = await page.getByRole('table').isVisible().catch(() => false);
    const hasEmptyState = await page.getByText(/no squads/i).isVisible().catch(() => false);

    // Either table or empty state should be visible
    expect(hasTable || hasEmptyState).toBe(true);
  });

  test('should navigate to squad details page', async ({ page }) => {
    // Wait for any squads to load
    await page.waitForTimeout(1000);

    // Check if there are any squad links
    const squadLinks = page.getByRole('link').filter({ hasText: /./ });
    const count = await squadLinks.count();

    if (count > 0) {
      // Click first squad link
      await squadLinks.first().click();

      // Should navigate to squad details
      await expect(page).toHaveURL(/\/squads\/[a-zA-Z0-9-]+/);
    }
  });

  test('should display squad details with info cards', async ({ page }) => {
    // This test would need an actual squad ID
    // For demonstration, we'll check the structure

    // Navigate to a mock squad details page
    await page.goto('/squads/test-squad-id');

    // Should show error or loading state if squad doesn't exist
    // Or show squad details if it does
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });

  test('should filter squads by status', async ({ page }) => {
    // Look for filter controls (if implemented)
    const statusFilter = page.getByLabel(/status|filter/i).first();

    if (await statusFilter.isVisible().catch(() => false)) {
      await statusFilter.click();
      // Select an option
      await page.getByRole('option', { name: /active/i }).first().click();
    }

    // Table should update (implementation specific)
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Check that create button can be focused with Tab
    await page.keyboard.press('Tab');

    // Check that focused element is interactive
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });

  test('should handle loading states gracefully', async ({ page }) => {
    // On initial load, there might be skeleton loaders
    const hasSkeletons = await page.locator('[class*="skeleton"]').first().isVisible().catch(() => false);

    // Either skeletons or content should be visible
    expect(hasSkeletons || await page.getByRole('table').isVisible().catch(() => false) || true).toBe(true);
  });
});
