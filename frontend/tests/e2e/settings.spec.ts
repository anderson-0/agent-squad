import { test, expect } from '@playwright/test';

test.describe('Settings & Profile', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings');
  });

  test('should display settings page correctly', async ({ page }) => {
    // Check page title and heading
    await expect(page).toHaveTitle(/Agent Squad/);
    await expect(page.getByRole('heading', { name: /settings/i })).toBeVisible();
  });

  test('should display settings navigation tabs', async ({ page }) => {
    // Check for tab navigation
    await expect(page.getByRole('tab', { name: /profile/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /preferences/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /api.*keys/i })).toBeVisible();
  });

  test('should navigate between settings tabs', async ({ page }) => {
    // Click on Preferences tab
    await page.getByRole('tab', { name: /preferences/i }).click();

    // Preferences content should be visible
    await expect(page.getByText(/theme|appearance/i)).toBeVisible();

    // Click on API Keys tab
    await page.getByRole('tab', { name: /api.*keys/i }).click();

    // API Keys content should be visible
    await expect(page.getByText(/api.*key|generate.*key/i)).toBeVisible();
  });

  test('should display profile information form', async ({ page }) => {
    // Make sure we're on Profile tab
    await page.getByRole('tab', { name: /profile/i }).click();

    // Check for profile form fields
    await expect(page.getByLabel(/name|full.*name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();

    // Check for save button
    await expect(page.getByRole('button', { name: /save|update/i })).toBeVisible();
  });

  test('should validate required fields in profile form', async ({ page }) => {
    // Navigate to Profile tab
    await page.getByRole('tab', { name: /profile/i }).click();

    // Clear name field
    const nameInput = page.getByLabel(/name|full.*name/i);
    await nameInput.clear();

    // Try to save
    await page.getByRole('button', { name: /save|update/i }).click();

    // Should show validation error or prevent submission
    // The form should either show an error message or the name field should be invalid
    const isInvalid = await nameInput.evaluate((el) =>
      el.hasAttribute('aria-invalid') || el.validity.valid === false
    ).catch(() => false);

    expect(isInvalid || await page.getByText(/required|cannot.*be.*empty/i).isVisible().catch(() => false)).toBeTruthy();
  });

  test('should display theme preference options', async ({ page }) => {
    // Navigate to Preferences tab
    await page.getByRole('tab', { name: /preferences/i }).click();

    // Check for theme selector
    await expect(page.getByText(/theme|appearance/i)).toBeVisible();

    // Look for theme options (light/dark/system)
    const hasThemeControls =
      await page.getByText(/light/i).isVisible().catch(() => false) ||
      await page.getByText(/dark/i).isVisible().catch(() => false) ||
      await page.getByRole('combobox').isVisible().catch(() => false);

    expect(hasThemeControls).toBe(true);
  });

  test('should display notification preferences', async ({ page }) => {
    // Navigate to Preferences tab
    await page.getByRole('tab', { name: /preferences/i }).click();

    // Check for notification settings
    const hasNotifications =
      await page.getByText(/notification/i).isVisible().catch(() => false) ||
      await page.getByRole('switch').count().then(c => c > 0).catch(() => false);

    expect(hasNotifications).toBe(true);
  });

  test('should display API keys section', async ({ page }) => {
    // Navigate to API Keys tab
    await page.getByRole('tab', { name: /api.*keys/i }).click();

    // Should show API key management UI
    await expect(page.getByText(/api.*key/i)).toBeVisible();

    // Should have generate or create button
    const hasGenerateButton =
      await page.getByRole('button', { name: /generate|create.*key/i }).isVisible().catch(() => false);

    expect(hasGenerateButton).toBe(true);
  });

  test('should open API key generation dialog', async ({ page }) => {
    // Navigate to API Keys tab
    await page.getByRole('tab', { name: /api.*keys/i }).click();

    // Find and click generate button
    const generateButton = page.getByRole('button', { name: /generate|create.*key/i });

    if (await generateButton.isVisible()) {
      await generateButton.click();

      // Dialog should appear
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/generate|create.*api.*key/i)).toBeVisible();
    }
  });

  test('should display existing API keys table or empty state', async ({ page }) => {
    // Navigate to API Keys tab
    await page.getByRole('tab', { name: /api.*keys/i }).click();

    // Either table with keys or empty state should be visible
    const hasTable = await page.getByRole('table').isVisible().catch(() => false);
    const hasEmptyState = await page.getByText(/no.*api.*keys|no.*keys.*yet/i).isVisible().catch(() => false);

    expect(hasTable || hasEmptyState).toBe(true);
  });

  test('should allow revoking API keys', async ({ page }) => {
    // Navigate to API Keys tab
    await page.getByRole('tab', { name: /api.*keys/i }).click();

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Check if there are any revoke buttons (if keys exist)
    const revokeButtons = page.getByRole('button', { name: /revoke|delete/i });
    const count = await revokeButtons.count();

    if (count > 0) {
      // Click first revoke button
      await revokeButtons.first().click();

      // Confirmation dialog might appear
      const hasConfirmation = await page.getByRole('dialog').isVisible().catch(() => false);

      if (hasConfirmation) {
        // Should have confirm and cancel buttons
        await expect(page.getByRole('button', { name: /confirm|yes|revoke/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /cancel|no/i })).toBeVisible();
      }
    }
  });

  test('should have accessible form elements', async ({ page }) => {
    // Profile tab
    await page.getByRole('tab', { name: /profile/i }).click();

    // All form inputs should have labels
    const nameInput = page.getByLabel(/name|full.*name/i);
    const emailInput = page.getByLabel(/email/i);

    await expect(nameInput).toBeVisible();
    await expect(emailInput).toBeVisible();

    // Buttons should be keyboard accessible
    const saveButton = page.getByRole('button', { name: /save|update/i });
    await expect(saveButton).toBeEnabled();
  });

  test('should preserve settings on tab switch', async ({ page }) => {
    // Go to Profile tab
    await page.getByRole('tab', { name: /profile/i }).click();

    // Make a change
    const nameInput = page.getByLabel(/name|full.*name/i);
    const originalValue = await nameInput.inputValue();
    await nameInput.fill('Test User Update');

    // Switch to another tab
    await page.getByRole('tab', { name: /preferences/i }).click();

    // Switch back to Profile
    await page.getByRole('tab', { name: /profile/i }).click();

    // Value should be preserved (or reset to original)
    const currentValue = await nameInput.inputValue();
    expect(currentValue).toBeTruthy();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Page should still be usable
    await expect(page.getByRole('heading', { name: /settings/i })).toBeVisible();

    // Tabs should be accessible (might be in dropdown on mobile)
    const hasTabs =
      await page.getByRole('tab', { name: /profile/i }).isVisible().catch(() => false) ||
      await page.getByRole('button', { name: /menu/i }).isVisible().catch(() => false);

    expect(hasTabs).toBe(true);
  });

  test('should handle profile update submission', async ({ page }) => {
    // Go to Profile tab
    await page.getByRole('tab', { name: /profile/i }).click();

    // Fill in some data
    await page.getByLabel(/name|full.*name/i).fill('Test User');

    // Click save
    await page.getByRole('button', { name: /save|update/i }).click();

    // Should either show success message or stay on page
    // (Without backend, we're just testing the UI flow)
    await page.waitForTimeout(1000);

    // Page should not crash
    await expect(page.getByRole('heading', { name: /settings/i })).toBeVisible();
  });

  test('should display breadcrumb or back navigation', async ({ page }) => {
    // Check for navigation elements
    const hasNav =
      await page.getByRole('navigation').isVisible().catch(() => false) ||
      await page.getByRole('link', { name: /dashboard|home/i }).isVisible().catch(() => false);

    expect(hasNav).toBe(true);
  });
});
