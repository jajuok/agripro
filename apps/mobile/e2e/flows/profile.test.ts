import { device, element, by, expect, waitFor } from 'detox';
import { login, logout, navigateToTab, DEMO_CREDENTIALS } from '../utils/testHelpers';
import { waitForVisible, waitForText, scrollToElement } from '../utils/waitHelpers';

describe('Profile Screen', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true, delete: true });
    await login(DEMO_CREDENTIALS.phone, DEMO_CREDENTIALS.pin);
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    await navigateToTab('tab-profile');
    await waitForVisible('profile-screen', 10000);
  });

  it('should display profile header with user info', async () => {
    await expect(element(by.id('profile-header'))).toBeVisible();
    await expect(element(by.id('profile-avatar'))).toBeVisible();
    await expect(element(by.id('profile-name'))).toBeVisible();
    await expect(element(by.id('profile-email'))).toBeVisible();
  });

  it('should display KYC verified badge', async () => {
    await waitForVisible('profile-verified-badge', 10000);

    await expect(element(by.id('profile-verified-text'))).toBeVisible();
    await expect(element(by.text('KYC Verified'))).toBeVisible();
  });

  it('should display profile stats', async () => {
    await waitForVisible('profile-stats', 10000);

    await expect(element(by.id('profile-stat-farms'))).toBeVisible();
    await expect(element(by.id('profile-stat-hectares'))).toBeVisible();
    await expect(element(by.id('profile-stat-schemes'))).toBeVisible();

    // Verify stat labels
    await expect(element(by.text('Farms'))).toBeVisible();
    await expect(element(by.text('Hectares'))).toBeVisible();
    await expect(element(by.text('Schemes'))).toBeVisible();
  });

  it('should display profile menu items', async () => {
    // Scroll down to see menu items - use larger scroll amount
    await element(by.id('profile-screen')).scroll(300, 'down');

    await waitFor(element(by.id('profile-menu-edit')))
      .toBeVisible()
      .withTimeout(5000);

    await expect(element(by.id('profile-menu-edit'))).toBeVisible();
  });

  it('should display app version', async () => {
    // Use scrollToElement helper to swipe until version is visible
    await scrollToElement('profile-screen', 'profile-version');
  });

  it('should logout successfully', async () => {
    // Use scrollToElement helper to swipe until logout button is visible
    await scrollToElement('profile-screen', 'profile-logout-button');

    await element(by.id('profile-logout-button')).tap();

    // Verify redirected to login screen
    await waitForVisible('login-screen', 10000);
    await expect(element(by.id('login-title'))).toBeVisible();
  });
});
