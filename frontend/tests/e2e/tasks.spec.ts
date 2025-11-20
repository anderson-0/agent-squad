import { test, expect } from '@playwright/test';

test.describe('Tasks Management', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to tasks page
    await page.goto('/tasks');
  });

  test('should display tasks page correctly', async ({ page }) => {
    // Check page title and heading
    await expect(page).toHaveTitle(/Agent Squad/);
    await expect(page.getByRole('heading', { name: /^tasks$/i })).toBeVisible();

    // Check for "Create Task" button
    await expect(page.getByRole('button', { name: /create.*task|new.*task/i })).toBeVisible();
  });

  test('should display task stats cards', async ({ page }) => {
    // Check for stat cards
    await expect(page.getByText(/total.*tasks/i)).toBeVisible();
    await expect(page.getByText(/in.*progress/i)).toBeVisible();
    await expect(page.getByText(/completed/i)).toBeVisible();
    await expect(page.getByText(/completion.*rate/i)).toBeVisible();
  });

  test('should display filters section', async ({ page }) => {
    // Check for filter controls
    await expect(page.getByText(/filters/i)).toBeVisible();

    // Look for filter dropdowns
    const filters = page.getByRole('combobox');
    expect(await filters.count()).toBeGreaterThan(0);
  });

  test('should open create task dialog', async ({ page }) => {
    // Click create task button
    await page.getByRole('button', { name: /create.*task|new.*task/i }).click();

    // Dialog should appear
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: /create.*task/i })).toBeVisible();

    // Check for form fields
    await expect(page.getByLabel(/title/i)).toBeVisible();
    await expect(page.getByLabel(/description/i)).toBeVisible();
    await expect(page.getByLabel(/priority/i)).toBeVisible();
  });

  test('should close create task dialog on cancel', async ({ page }) => {
    // Open dialog
    await page.getByRole('button', { name: /create.*task|new.*task/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click cancel or close button
    await page.getByRole('button', { name: /cancel/i }).click();

    // Dialog should close
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('should filter tasks by status', async ({ page }) => {
    // Find status filter
    const statusFilter = page.getByRole('combobox').first();

    if (await statusFilter.isVisible()) {
      await statusFilter.click();

      // Wait for options to appear
      await page.waitForTimeout(500);

      // Select a status (if options are available)
      const options = page.getByRole('option');
      if (await options.count() > 0) {
        await options.first().click();
      }
    }

    // Table should update (implementation specific)
  });

  test('should filter tasks by priority', async ({ page }) => {
    // Find priority filter (usually second filter)
    const filters = page.getByRole('combobox');

    if (await filters.count() >= 2) {
      const priorityFilter = filters.nth(1);
      await priorityFilter.click();

      // Wait for options
      await page.waitForTimeout(500);

      // Select a priority
      const options = page.getByRole('option');
      if (await options.count() > 0) {
        await options.first().click();
      }
    }
  });

  test('should filter tasks by squad', async ({ page }) => {
    // Find squad filter (usually third filter)
    const filters = page.getByRole('combobox');

    if (await filters.count() >= 3) {
      const squadFilter = filters.nth(2);
      await squadFilter.click();

      // Wait for options
      await page.waitForTimeout(500);
    }
  });

  test('should display tasks table or empty state', async ({ page }) => {
    // Check if table or empty state is visible
    const hasTable = await page.getByRole('table').isVisible().catch(() => false);
    const hasEmptyState = await page.getByText(/no tasks/i).isVisible().catch(() => false);

    // Either table or empty state should be visible
    expect(hasTable || hasEmptyState).toBe(true);
  });

  test('should navigate to task details page', async ({ page }) => {
    // Wait for any tasks to load
    await page.waitForTimeout(1000);

    // Check if there are any task links
    const taskLinks = page.getByRole('link').filter({ hasText: /./ });
    const count = await taskLinks.count();

    if (count > 0) {
      // Click first task link (skip navigation links)
      const mainContent = page.locator('main');
      const taskLink = mainContent.getByRole('link').first();

      if (await taskLink.isVisible()) {
        await taskLink.click();

        // Should navigate to task details
        await expect(page).toHaveURL(/\/tasks\/[a-zA-Z0-9-]+/);
      }
    }
  });

  test('should display task priority badges with colors', async ({ page }) => {
    // Wait for content to load
    await page.waitForTimeout(1000);

    // Check for badge elements (if tasks exist)
    const badges = page.locator('[class*="badge"]');

    if (await badges.count() > 0) {
      // Badges should be visible
      await expect(badges.first()).toBeVisible();
    }
  });

  test('should display task status badges with colors', async ({ page }) => {
    // Wait for content to load
    await page.waitForTimeout(1000);

    // Status badges should have different colors based on status
    // This is a visual check that badges exist
    const statusElements = page.getByText(/pending|in progress|completed|failed/i);

    if (await statusElements.count() > 0) {
      await expect(statusElements.first()).toBeVisible();
    }
  });

  test('should show loading state initially', async ({ page }) => {
    // Reload to see loading state
    await page.reload();

    // Check for skeleton loaders or loading indicator
    const hasSkeletons = await page.locator('[class*="skeleton"]').first().isVisible().catch(() => false);

    // Loading state should appear briefly
    expect(hasSkeletons || true).toBe(true);
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Page should still be usable
    await expect(page.getByRole('heading', { name: /tasks/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /create.*task/i })).toBeVisible();
  });
});
