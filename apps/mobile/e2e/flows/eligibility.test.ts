import { device, element, by, expect, waitFor } from 'detox';
import { login, DEMO_CREDENTIALS, navigateToTab } from '../utils/testHelpers';
import { waitForVisible, scrollToElement } from '../utils/waitHelpers';

describe('Eligibility Workflow', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true, delete: true });
    await login(DEMO_CREDENTIALS.phone, DEMO_CREDENTIALS.pin);
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    // Navigate to home first
    await navigateToTab('tab-home');
    await waitForVisible('home-screen', 10000);
  });

  // Helper to scroll to and tap eligibility card
  const navigateToEligibilityList = async () => {
    // Use scrollToElement helper to swipe until eligibility card is visible
    await scrollToElement('home-screen', 'home-eligibility-card');

    await element(by.id('home-eligibility-card')).tap();
    await waitForVisible('eligibility-list-screen', 10000);
  };

  it('should navigate to eligibility list from home', async () => {
    await navigateToEligibilityList();
    await expect(element(by.id('eligibility-list-screen'))).toBeVisible();
  });

  it('should display eligibility list with stats', async () => {
    await navigateToEligibilityList();

    await expect(element(by.id('eligibility-list-title'))).toBeVisible();
    await expect(element(by.id('eligibility-list-stats'))).toBeVisible();
    await expect(element(by.id('eligibility-list-stat-available'))).toBeVisible();
    await expect(element(by.id('eligibility-list-stat-enrolled'))).toBeVisible();
    await expect(element(by.id('eligibility-list-stat-pending'))).toBeVisible();
  });

  it('should display scheme cards', async () => {
    await navigateToEligibilityList();

    await expect(element(by.id('eligibility-list-section-title'))).toBeVisible();

    // Wait for scheme cards to load
    await waitFor(element(by.id('eligibility-list-scheme-card-1')))
      .toBeVisible()
      .withTimeout(10000);
  });

  it('should navigate to scheme detail', async () => {
    await navigateToEligibilityList();

    await waitFor(element(by.id('eligibility-list-scheme-card-1')))
      .toBeVisible()
      .withTimeout(10000);

    await element(by.id('eligibility-list-scheme-card-1')).tap();

    await waitForVisible('eligibility-detail-screen', 10000);
    await expect(element(by.id('eligibility-detail-name'))).toBeVisible();
    await expect(element(by.id('eligibility-detail-type-tag'))).toBeVisible();
    await expect(element(by.id('eligibility-detail-info-card'))).toBeVisible();
  });

  it('should check eligibility and display assessment', async () => {
    await navigateToEligibilityList();

    await waitFor(element(by.id('eligibility-list-scheme-card-1')))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id('eligibility-list-scheme-card-1')).tap();

    await waitForVisible('eligibility-detail-screen', 10000);

    // Swipe to find check eligibility button
    await scrollToElement('eligibility-detail-screen', 'eligibility-detail-check-button');

    await element(by.id('eligibility-detail-check-button')).tap();

    // Wait for the check button to disappear (it hides when assessment loads)
    // This indicates the 2-second mock delay has completed
    await waitFor(element(by.id('eligibility-detail-check-button')))
      .not.toExist()
      .withTimeout(10000);

    // Give React time to render the assessment section
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // The assessment section should now be visible - try scrolling to find it
    // Use multiple swipes to ensure we find it
    for (let i = 0; i < 5; i++) {
      try {
        await waitFor(element(by.id('eligibility-detail-assessment')))
          .toBeVisible()
          .withTimeout(2000);
        break; // Found it
      } catch {
        // Swipe up to reveal more content
        await element(by.id('eligibility-detail-screen')).swipe('up', 'slow', 0.5);
      }
    }

    // Verify assessment elements are visible (scroll more if needed)
    await waitFor(element(by.id('eligibility-detail-assessment-title'))).toBeVisible().withTimeout(5000);

    // Scroll to see score cards if needed
    try {
      await waitFor(element(by.id('eligibility-detail-score-card'))).toBeVisible().withTimeout(3000);
    } catch {
      await element(by.id('eligibility-detail-screen')).swipe('up', 'slow', 0.3);
      await waitFor(element(by.id('eligibility-detail-score-card'))).toBeVisible().withTimeout(3000);
    }
  });

  it('should navigate back to list from detail', async () => {
    await navigateToEligibilityList();

    await waitFor(element(by.id('eligibility-list-scheme-card-1')))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id('eligibility-list-scheme-card-1')).tap();

    await waitForVisible('eligibility-detail-back-button', 10000);
    await element(by.id('eligibility-detail-back-button')).tap();

    await waitForVisible('eligibility-list-screen', 5000);
    await expect(element(by.id('eligibility-list-title'))).toBeVisible();
  });

  it('should navigate back to home from list', async () => {
    await navigateToEligibilityList();

    await waitForVisible('eligibility-list-back-button', 10000);
    await element(by.id('eligibility-list-back-button')).tap();

    // Wait for home screen to appear
    await waitForVisible('home-screen', 10000);

    // The home screen might be scrolled down, so scroll to top first
    await element(by.id('home-screen')).swipe('down', 'fast', 0.8);

    // Now home-greeting should be visible
    await waitFor(element(by.id('home-greeting'))).toBeVisible().withTimeout(5000);
  });
});
