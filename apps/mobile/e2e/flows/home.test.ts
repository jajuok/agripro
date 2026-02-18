import { device, element, by, expect, waitFor } from 'detox';
import { login, DEMO_CREDENTIALS, navigateToTab } from '../utils/testHelpers';
import { waitForVisible, scrollToElement } from '../utils/waitHelpers';

describe('Home Screen', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true, delete: true });
    await login(DEMO_CREDENTIALS.phone, DEMO_CREDENTIALS.pin);
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    // Navigate back to home if needed
    await navigateToTab('tab-home');
    await waitForVisible('home-screen', 10000);
  });

  it('should display greeting and overview', async () => {
    await expect(element(by.id('home-greeting'))).toBeVisible();
    await expect(element(by.id('home-sub-greeting'))).toBeVisible();
    await expect(element(by.text("Here's your farm overview"))).toBeVisible();
  });

  it('should display stats container with farm data', async () => {
    await waitForVisible('home-stats-container', 10000);

    await expect(element(by.id('home-stat-farms'))).toBeVisible();
    await expect(element(by.id('home-stat-hectares'))).toBeVisible();
    await expect(element(by.id('home-stat-crops'))).toBeVisible();
  });

  it('should display Quick Actions section', async () => {
    await waitForVisible('home-section-quick-actions', 10000);

    await expect(element(by.text('Quick Actions'))).toBeVisible();
    await expect(element(by.id('home-action-add-farm'))).toBeVisible();
    await expect(element(by.id('home-action-check-eligibility'))).toBeVisible();
    await expect(element(by.id('home-action-record-location'))).toBeVisible();
    await expect(element(by.id('home-action-view-reports'))).toBeVisible();
  });

  it('should display KYC status card', async () => {
    await waitForVisible('home-kyc-card', 10000);

    await expect(element(by.id('home-kyc-status'))).toBeVisible();
    await expect(element(by.text('Verified'))).toBeVisible();
  });

  it('should display eligibility card and navigate on tap', async () => {
    // Use scrollToElement helper to swipe until eligibility card is visible
    await scrollToElement('home-screen', 'home-eligibility-card');

    await element(by.id('home-eligibility-card')).tap();

    await waitForVisible('eligibility-list-screen', 10000);
    await expect(element(by.id('eligibility-list-title'))).toBeVisible();
  });
});
