import { device, element, by, expect } from 'detox';
import { login, navigateToTab, DEMO_CREDENTIALS } from '../utils/testHelpers';
import { waitForVisible, waitForText } from '../utils/waitHelpers';

describe('Tab Navigation', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true, delete: true });
    await login(DEMO_CREDENTIALS.email, DEMO_CREDENTIALS.password);
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should navigate to Home tab', async () => {
    await navigateToTab('tab-home');

    await waitForVisible('home-screen', 10000);
    await expect(element(by.id('home-greeting'))).toBeVisible();
  });

  it('should navigate to Farms tab', async () => {
    await navigateToTab('tab-farms');

    await waitForVisible('farms-screen', 10000);
  });

  it('should navigate to Tasks tab', async () => {
    await navigateToTab('tab-tasks');

    await waitForVisible('tasks-screen', 10000);
  });

  it('should navigate to Market tab', async () => {
    await navigateToTab('tab-market');

    await waitForVisible('market-screen', 10000);
  });

  it('should navigate to Profile tab', async () => {
    await navigateToTab('tab-profile');

    await waitForVisible('profile-screen', 10000);
    await expect(element(by.id('profile-name'))).toBeVisible();
    await expect(element(by.id('profile-verified-text'))).toBeVisible();
  });

  it('should navigate through all tabs sequentially', async () => {
    // Home
    await navigateToTab('tab-home');
    await waitForVisible('home-screen', 5000);

    // Farms
    await navigateToTab('tab-farms');
    await waitForVisible('farms-screen', 5000);

    // Tasks
    await navigateToTab('tab-tasks');
    await waitForVisible('tasks-screen', 5000);

    // Market
    await navigateToTab('tab-market');
    await waitForVisible('market-screen', 5000);

    // Profile
    await navigateToTab('tab-profile');
    await waitForVisible('profile-screen', 5000);

    // Back to Home
    await navigateToTab('tab-home');
    await waitForVisible('home-greeting', 5000);
  });
});
