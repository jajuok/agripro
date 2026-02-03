import { device, element, by, expect, waitFor } from 'detox';
import {
  generateTestData,
  login,
  logout,
  DEMO_CREDENTIALS,
} from '../utils/testHelpers';
import { scrollToElement } from '../utils/waitHelpers';
import { waitForVisible, waitForText } from '../utils/waitHelpers';

describe('Authentication Flows', () => {
  describe('Login Flow', () => {
    beforeAll(async () => {
      await device.launchApp({ newInstance: true, delete: true });
    });

    beforeEach(async () => {
      await device.reloadReactNative();
    });

    it('should display login screen elements', async () => {
      await waitForVisible('login-screen', 15000);

      await expect(element(by.id('login-title'))).toBeVisible();
      await expect(element(by.id('login-subtitle'))).toBeVisible();
      await expect(element(by.id('login-email-input'))).toBeVisible();
      await expect(element(by.id('login-password-input'))).toBeVisible();
      await expect(element(by.id('login-submit-button'))).toBeVisible();
      await expect(element(by.id('login-register-link'))).toBeVisible();
    });

    it('should show error for invalid credentials', async () => {
      await waitForVisible('login-email-input', 15000);

      await element(by.id('login-email-input')).tap();
      await element(by.id('login-email-input')).typeText('invalid@test.com');

      await element(by.id('login-password-input')).tap();
      await element(by.id('login-password-input')).typeText('wrongpassword');

      await element(by.id('login-submit-button')).tap();

      await waitForVisible('login-error', 10000);
      await expect(element(by.id('login-error'))).toBeVisible();
    });

    it('should login successfully with valid credentials', async () => {
      await waitForVisible('login-email-input', 15000);

      await login(DEMO_CREDENTIALS.email, DEMO_CREDENTIALS.password);

      await expect(element(by.id('home-screen'))).toBeVisible();
      await expect(element(by.id('home-greeting'))).toBeVisible();
    });

    it('should logout successfully', async () => {
      // Launch fresh to ensure clean state
      await device.launchApp({ newInstance: true, delete: true });

      await login(DEMO_CREDENTIALS.email, DEMO_CREDENTIALS.password);
      await logout();

      await expect(element(by.id('login-screen'))).toBeVisible();
      await expect(element(by.id('login-email-input'))).toBeVisible();
    });
  });

  describe('Registration Flow', () => {
    beforeEach(async () => {
      await device.launchApp({ newInstance: true, delete: true });
    });

    it('should navigate to registration screen', async () => {
      await waitForVisible('login-register-link', 15000);

      await element(by.id('login-register-link')).tap();

      await waitForText('Create Account', 10000);
      await expect(element(by.text('Join AgriScheme Pro'))).toBeVisible();
    });

    it('should display all registration form fields', async () => {
      await waitForVisible('login-register-link', 15000);
      await element(by.id('login-register-link')).tap();

      await waitForText('Create Account', 10000);

      await expect(element(by.id('firstname-input'))).toBeVisible();
      await expect(element(by.id('lastname-input'))).toBeVisible();
      await expect(element(by.id('email-input'))).toBeVisible();
      await expect(element(by.id('phone-input'))).toBeVisible();
    });

    it('should complete registration with unique data', async () => {
      const testData = generateTestData();

      await waitForVisible('login-register-link', 15000);
      await element(by.id('login-register-link')).tap();
      await waitForText('Create Account', 10000);

      // Fill form - use replaceText to avoid keyboard issues
      await element(by.id('firstname-input')).tap();
      await element(by.id('firstname-input')).replaceText(testData.firstName);

      await element(by.id('lastname-input')).tap();
      await element(by.id('lastname-input')).replaceText(testData.lastName);

      await element(by.id('email-input')).tap();
      await element(by.id('email-input')).replaceText(testData.email);

      await element(by.id('phone-input')).tap();
      await element(by.id('phone-input')).replaceText(testData.phone);

      // Hide keyboard before scrolling
      await device.pressBack();
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Scroll to password fields using swipe
      await scrollToElement('register-screen', 'password-input');

      await element(by.id('password-input')).tap();
      await element(by.id('password-input')).replaceText(testData.password);

      // Hide keyboard before scrolling to confirm password
      await device.pressBack();
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Scroll to confirm password field
      await scrollToElement('register-screen', 'confirm-password-input');

      await element(by.id('confirm-password-input')).tap();
      await element(by.id('confirm-password-input')).replaceText(testData.password);

      // Hide keyboard before scrolling to register button
      await device.pressBack();
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Scroll to register button and tap
      await scrollToElement('register-screen', 'register-button');

      await element(by.id('register-button')).tap();

      // Wait for registration to complete - home screen should appear
      // First wait a moment for navigation to initiate
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Now look for home screen elements with longer timeout
      // Try multiple home screen elements in case one is more reliable
      try {
        await waitFor(element(by.id('home-screen')))
          .toBeVisible()
          .withTimeout(30000);
      } catch {
        // If home-screen not found, check if we're still on register screen with error
        try {
          await waitFor(element(by.id('register-error')))
            .toBeVisible()
            .withTimeout(3000);
          throw new Error('Registration failed - API returned error. Check backend services are running.');
        } catch (innerError) {
          // Neither found - rethrow original timeout error
          throw new Error('Navigation to home screen failed after registration');
        }
      }

      // Verify we're on the home screen
      await expect(element(by.id('home-screen'))).toBeVisible();
      // home-greeting should be visible within the home screen
      await waitFor(element(by.id('home-greeting'))).toBeVisible().withTimeout(5000);
    });
  });
});
