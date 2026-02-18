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
 * Login with provided credentials (phone + PIN)
 */
export const login = async (phone: string, pin: string) => {
  await waitFor(element(by.id('login-screen')))
    .toBeVisible()
    .withTimeout(15000);

  // Phone input may be hidden if a cached phone is shown
  try {
    await waitFor(element(by.id('login-phone-input')))
      .toBeVisible()
      .withTimeout(3000);

    await element(by.id('login-phone-input')).tap();
    await element(by.id('login-phone-input')).clearText();
    await element(by.id('login-phone-input')).typeText(phone);
  } catch {
    // Cached phone shown — tap "Not you?" to show phone field
    try {
      await element(by.id('login-change-phone')).tap();
      await waitFor(element(by.id('login-phone-input')))
        .toBeVisible()
        .withTimeout(5000);
      await element(by.id('login-phone-input')).tap();
      await element(by.id('login-phone-input')).clearText();
      await element(by.id('login-phone-input')).typeText(phone);
    } catch {
      // Phone field may already be pre-filled, continue to PIN
    }
  }

  await element(by.id('login-pin-input')).tap();
  await element(by.id('login-pin-input')).typeText(pin);

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
 * Demo credentials for testing (phone + PIN)
 */
export const DEMO_CREDENTIALS = {
  phone: '+254799999999',
  pin: '1234',
};
