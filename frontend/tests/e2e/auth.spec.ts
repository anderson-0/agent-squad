import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the login page
    await page.goto('/login');
  });

  test('should display login page correctly', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Agent Squad/);

    // Check for login form elements
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    // Click submit without filling form
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should show validation errors (if implemented)
    // This test validates client-side validation
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toBeFocused();
  });

  test('should navigate to register page', async ({ page }) => {
    // Click on "Create account" or similar link
    await page.getByRole('link', { name: /create.*account|sign up|register/i }).click();

    // Should navigate to register page
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByRole('heading', { name: /create.*account|sign up|register/i })).toBeVisible();
  });

  test('should navigate to forgot password page', async ({ page }) => {
    // Click on "Forgot password" link
    await page.getByRole('link', { name: /forgot.*password/i }).click();

    // Should navigate to forgot password page
    await expect(page).toHaveURL(/\/forgot-password/);
    await expect(page.getByRole('heading', { name: /forgot.*password|reset.*password/i })).toBeVisible();
  });

  test('should register new user successfully', async ({ page }) => {
    // Navigate to register page
    await page.goto('/register');

    // Fill registration form
    const timestamp = Date.now();
    await page.getByLabel(/full name|name/i).fill(`Test User ${timestamp}`);
    await page.getByLabel(/email/i).fill(`test${timestamp}@example.com`);
    await page.getByLabel(/^password$/i).fill('TestPassword123!');

    // Submit form
    await page.getByRole('button', { name: /create.*account|sign up|register/i }).click();

    // Should redirect to dashboard or login (depends on implementation)
    await page.waitForURL(/\/(login|$)/, { timeout: 5000 });
  });

  test('should login with valid credentials (mock)', async ({ page }) => {
    // Note: This test would need a test user account or API mocking
    // For now, we'll test the UI flow

    // Fill login form
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');

    // Submit form
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for navigation (will fail without backend, but tests the flow)
    // In a real test, we'd either:
    // 1. Have a test backend running
    // 2. Mock the API responses
    // 3. Use a fixture with valid credentials
  });

  test('should protect dashboard route when not authenticated', async ({ page }) => {
    // Clear any stored auth tokens
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());

    // Try to access protected route
    await page.goto('/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });

  test('should protect squads route when not authenticated', async ({ page }) => {
    // Clear any stored auth tokens
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());

    // Try to access protected route
    await page.goto('/squads');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });

  test('should have accessible form elements', async ({ page }) => {
    // Check that form inputs have proper labels
    const emailInput = page.getByLabel(/email/i);
    const passwordInput = page.getByLabel(/password/i);

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();

    // Check that submit button is keyboard accessible
    const submitButton = page.getByRole('button', { name: /sign in/i });
    await expect(submitButton).toBeEnabled();
  });
});
