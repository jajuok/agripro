import { element, by, waitFor } from 'detox';

/**
 * Wait for element to be visible with custom timeout
 */
export const waitForVisible = async (testId: string, timeout = 10000) => {
  await waitFor(element(by.id(testId))).toBeVisible().withTimeout(timeout);
};

/**
 * Wait for element to exist (may not be visible)
 */
export const waitForExist = async (testId: string, timeout = 10000) => {
  await waitFor(element(by.id(testId))).toExist().withTimeout(timeout);
};

/**
 * Wait for text to be visible
 */
export const waitForText = async (text: string, timeout = 10000) => {
  await waitFor(element(by.text(text))).toBeVisible().withTimeout(timeout);
};

/**
 * Wait for element to not be visible
 */
export const waitForNotVisible = async (testId: string, timeout = 10000) => {
  await waitFor(element(by.id(testId))).not.toBeVisible().withTimeout(timeout);
};

/**
 * Scroll until element is visible using swipe gesture
 * Note: 'up' swipe direction reveals content below
 */
export const scrollToElement = async (
  scrollViewId: string,
  targetId: string,
  direction: 'up' | 'down' = 'up',
  speed: 'fast' | 'slow' = 'slow',
  maxSwipes = 10
) => {
  for (let i = 0; i < maxSwipes; i++) {
    try {
      await waitFor(element(by.id(targetId))).toBeVisible().withTimeout(1500);
      return; // Element is visible, exit
    } catch {
      // Element not visible, swipe and try again
      await element(by.id(scrollViewId)).swipe(direction, speed, 0.5);
    }
  }
  // Final check - throw if still not visible
  await waitFor(element(by.id(targetId))).toBeVisible().withTimeout(3000);
};
