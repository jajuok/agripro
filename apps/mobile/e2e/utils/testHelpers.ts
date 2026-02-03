import { element, by, expect, waitFor, device } from 'detox';
import { scrollToElement } from './waitHelpers';

/**
 * Generate unique test data for registration
 */
export const generateTestData = () => {
  const timestamp = Date.now();
  return {
    // Use .example.com which is a valid reserved domain for testing per RFC 2606
    email: `test_${timestamp}@example.com`,
    phone: `+254${Math.floor(700000000 + Math.random() * 99999999)}`,
    password: 'TestPass123!',
    firstName: 'Test',
    lastName: 'Farmer',
  };
};

/**
 * Login with provided credentials
 */
export const login = async (email: string, password: string) => {
  await waitFor(element(by.id('login-screen')))
    .toBeVisible()
    .withTimeout(15000);

  await waitFor(element(by.id('login-email-input')))
    .toBeVisible()
    .withTimeout(10000);

  await element(by.id('login-email-input')).tap();
  await element(by.id('login-email-input')).typeText(email);

  await element(by.id('login-password-input')).tap();
  await element(by.id('login-password-input')).typeText(password);

  await element(by.id('login-submit-button')).tap();

  await waitFor(element(by.id('home-greeting')))
    .toBeVisible()
    .withTimeout(15000);
};

/**
 * Logout from the app
 */
export const logout = async () => {
  // First ensure we're on the profile tab
  await waitFor(element(by.id('tab-profile')))
    .toBeVisible()
    .withTimeout(5000);

  await element(by.id('tab-profile')).tap();

  await waitFor(element(by.id('profile-screen')))
    .toBeVisible()
    .withTimeout(10000);

  // Use scrollToElement helper to swipe until logout button is visible
  await scrollToElement('profile-screen', 'profile-logout-button');

  await element(by.id('profile-logout-button')).tap();

  // Wait for login screen to appear
  await waitFor(element(by.id('login-screen')))
    .toBeVisible()
    .withTimeout(10000);
};

/**
 * Clear app state and ensure logged out
 */
export const ensureLoggedOut = async () => {
  await device.launchApp({ newInstance: true, delete: true });

  // Wait for either login screen or home screen
  try {
    await waitFor(element(by.id('login-screen')))
      .toBeVisible()
      .withTimeout(5000);
  } catch {
    // If home screen is visible, logout
    await logout();
  }
};

/**
 * Navigate to a specific tab
 */
export const navigateToTab = async (tabId: string) => {
  await waitFor(element(by.id(tabId)))
    .toBeVisible()
    .withTimeout(5000);
  await element(by.id(tabId)).tap();
  await new Promise((resolve) => setTimeout(resolve, 500)); // Wait for animation
};

/**
 * Demo credentials for testing
 */
export const DEMO_CREDENTIALS = {
  email: 'demo@agripro.com',
  password: 'Demo1234X',
};
