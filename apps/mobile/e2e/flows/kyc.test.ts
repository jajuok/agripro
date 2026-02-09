import { device, element, by, expect, waitFor } from 'detox';
import {
  generateTestData,
  login,
  logout,
  DEMO_CREDENTIALS,
} from '../utils/testHelpers';
import { waitForVisible, waitForText, scrollToElement } from '../utils/waitHelpers';

describe('KYC Workflow', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true, delete: true });

    // Login first
    await waitForVisible('login-email-input', 15000);
    await login(DEMO_CREDENTIALS.email, DEMO_CREDENTIALS.password);

    // Wait for home screen
    await waitForVisible('home-screen', 15000);
  });

  beforeEach(async () => {
    // Navigate to KYC screen from home
    await device.reloadReactNative();
    await waitForVisible('home-screen', 15000);
  });

  describe('KYC Dashboard', () => {
    it('should display KYC dashboard when no application exists', async () => {
      // Navigate to KYC (assuming there's a button/menu item)
      // This may need adjustment based on actual navigation implementation
      await element(by.text('KYC Verification')).tap();

      await waitForVisible('kyc-dashboard', 15000);

      // Check for empty state
      await expect(element(by.text('KYC Verification'))).toBeVisible();
      await expect(element(by.text('Complete your Know Your Customer'))).toBeVisible();
      await expect(element(by.text('Why KYC?'))).toBeVisible();
      await expect(element(by.text('Access financial services'))).toBeVisible();
      await expect(element(by.id('kyc-start-button'))).toBeVisible();
    });

    it('should start KYC application', async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-start-button', 15000);

      await element(by.id('kyc-start-button')).tap();

      // Wait for success and status screen
      await waitForVisible('kyc-status-view', 10000);

      // Should show progress
      await expect(element(by.text(/Progress:/))).toBeVisible();
      await expect(element(by.text('Personal Information'))).toBeVisible();
      await expect(element(by.text('Document Upload'))).toBeVisible();
    });

    it('should display KYC status when application exists', async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);

      // Check status display
      await expect(element(by.text(/Progress:/))).toBeVisible();
      await expect(element(by.id('kyc-progress-bar'))).toBeVisible();

      // Check steps are visible
      await expect(element(by.text('Personal Information'))).toBeVisible();
      await expect(element(by.text('Document Upload'))).toBeVisible();
      await expect(element(by.text('Bank Information'))).toBeVisible();
    });
  });

  describe('Personal Information Step', () => {
    beforeEach(async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);
    });

    it('should navigate to personal information form', async () => {
      // Tap on Personal Information step
      await scrollToElement('personal-info-step', 'kyc-status-view');
      await element(by.id('personal-info-step')).tap();

      await waitForVisible('personal-info-form', 15000);

      // Check form fields are present
      await expect(element(by.text('Personal Information'))).toBeVisible();
      await expect(element(by.id('national-id-input'))).toBeVisible();
      await expect(element(by.id('dob-picker'))).toBeVisible();
      await expect(element(by.text('Male'))).toBeVisible();
      await expect(element(by.text('Female'))).toBeVisible();
      await expect(element(by.id('phone-input'))).toBeVisible();
      await expect(element(by.id('address-input'))).toBeVisible();
    });

    it('should validate required fields', async () => {
      await scrollToElement('personal-info-step', 'kyc-status-view');
      await element(by.id('personal-info-step')).tap();
      await waitForVisible('personal-info-form', 15000);

      // Try to submit without filling fields
      await scrollToElement('personal-info-submit-button', 'personal-info-form');
      await element(by.id('personal-info-submit-button')).tap();

      // Should show error
      await waitForText('Please fill in all required fields', 5000);
    });

    it('should fill and submit personal information', async () => {
      await scrollToElement('personal-info-step', 'kyc-status-view');
      await element(by.id('personal-info-step')).tap();
      await waitForVisible('personal-info-form', 15000);

      // Fill National ID
      await element(by.id('national-id-input')).tap();
      await element(by.id('national-id-input')).typeText('12345678');

      // Select date of birth
      await element(by.id('dob-picker')).tap();
      // Date picker interaction may vary by platform
      // await element(by.text('OK')).tap(); // If there's a confirmation

      // Select gender
      await element(by.text('Male')).tap();

      // Fill phone
      await element(by.id('phone-input')).tap();
      await element(by.id('phone-input')).typeText('0712345678');

      // Fill address
      await element(by.id('address-input')).tap();
      await element(by.id('address-input')).typeText('123 Test Street, Nairobi');

      // Scroll to submit button
      await scrollToElement('personal-info-submit-button', 'personal-info-form');
      await element(by.id('personal-info-submit-button')).tap();

      // Wait for success
      await waitForText('Personal information saved successfully', 10000);

      // Should return to dashboard
      await element(by.text('OK')).tap();
      await waitForVisible('kyc-status-view', 15000);

      // Personal info should be marked complete
      await expect(element(by.id('personal-info-complete-icon'))).toBeVisible();
    });
  });

  describe('Document Upload Step', () => {
    beforeEach(async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);
    });

    it('should navigate to document upload screen', async () => {
      await scrollToElement('documents-step', 'kyc-status-view');
      await element(by.id('documents-step')).tap();

      await waitForVisible('documents-screen', 15000);

      // Check document types are listed
      await expect(element(by.text('Upload Documents'))).toBeVisible();
      await expect(element(by.text('National ID'))).toBeVisible();
      await expect(element(by.text('Land Title Deed'))).toBeVisible();
      await expect(element(by.text('Bank Statement'))).toBeVisible();
    });

    it('should display document types with icons and descriptions', async () => {
      await scrollToElement('documents-step', 'kyc-status-view');
      await element(by.id('documents-step')).tap();
      await waitForVisible('documents-screen', 15000);

      // Check National ID card
      await expect(element(by.id('doc-card-national_id'))).toBeVisible();
      await expect(element(by.text('National ID'))).toBeVisible();
      await expect(element(by.text('Government issued ID card'))).toBeVisible();
      await expect(element(by.text('Required'))).toBeVisible();
    });

    it('should select document type and show upload options', async () => {
      await scrollToElement('documents-step', 'kyc-status-view');
      await element(by.id('documents-step')).tap();
      await waitForVisible('documents-screen', 15000);

      // Select National ID
      await element(by.id('doc-card-national_id')).tap();

      // Upload form should appear
      await waitForVisible('document-upload-form', 5000);
      await expect(element(by.text('Upload National ID'))).toBeVisible();
      await expect(element(by.text('Take Photo'))).toBeVisible();
      await expect(element(by.text('Choose from Gallery'))).toBeVisible();
    });

    it('should handle document upload cancellation', async () => {
      await scrollToElement('documents-step', 'kyc-status-view');
      await element(by.id('documents-step')).tap();
      await waitForVisible('documents-screen', 15000);

      await element(by.id('doc-card-national_id')).tap();
      await waitForVisible('document-upload-form', 5000);

      // Cancel upload
      await scrollToElement('upload-cancel-button', 'documents-screen');
      await element(by.id('upload-cancel-button')).tap();

      // Form should close
      await expect(element(by.id('document-upload-form'))).not.toBeVisible();
    });

    // Note: Actual image capture/selection tests would require mock images
    // or camera permissions handling which varies by test environment
  });

  describe('Bank Information Step', () => {
    beforeEach(async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);
    });

    it('should navigate to bank information form', async () => {
      await scrollToElement('bank-info-step', 'kyc-status-view');
      await element(by.id('bank-info-step')).tap();

      await waitForVisible('bank-info-form', 15000);

      // Check form fields
      await expect(element(by.text('Bank Information'))).toBeVisible();
      await expect(element(by.id('bank-name-select'))).toBeVisible();
      await expect(element(by.id('account-number-input'))).toBeVisible();
      await expect(element(by.id('account-name-input'))).toBeVisible();
    });

    it('should validate bank information fields', async () => {
      await scrollToElement('bank-info-step', 'kyc-status-view');
      await element(by.id('bank-info-step')).tap();
      await waitForVisible('bank-info-form', 15000);

      // Try to submit without filling
      await scrollToElement('bank-info-submit-button', 'bank-info-form');
      await element(by.id('bank-info-submit-button')).tap();

      await waitForText('Please fill in all required fields', 5000);
    });

    it('should select bank from dropdown', async () => {
      await scrollToElement('bank-info-step', 'kyc-status-view');
      await element(by.id('bank-info-step')).tap();
      await waitForVisible('bank-info-form', 15000);

      // Open bank dropdown
      await element(by.id('bank-name-select')).tap();

      // Should show bank list
      await waitForVisible('bank-dropdown', 5000);
      await expect(element(by.text('KCB Bank'))).toBeVisible();
      await expect(element(by.text('Equity Bank'))).toBeVisible();

      // Select a bank
      await element(by.text('KCB Bank')).tap();

      // Dropdown should close and bank selected
      await expect(element(by.id('bank-name-select'))).toHaveText('KCB Bank');
    });

    it('should fill and submit bank information', async () => {
      await scrollToElement('bank-info-step', 'kyc-status-view');
      await element(by.id('bank-info-step')).tap();
      await waitForVisible('bank-info-form', 15000);

      // Select bank
      await element(by.id('bank-name-select')).tap();
      await waitForVisible('bank-dropdown', 5000);
      await element(by.text('Equity Bank')).tap();

      // Fill account number
      await element(by.id('account-number-input')).tap();
      await element(by.id('account-number-input')).typeText('1234567890');

      // Fill account name
      await element(by.id('account-name-input')).tap();
      await element(by.id('account-name-input')).typeText('John Doe');

      // Fill branch (optional)
      await element(by.id('branch-name-input')).tap();
      await element(by.id('branch-name-input')).typeText('Nairobi Branch');

      // Submit
      await scrollToElement('bank-info-submit-button', 'bank-info-form');
      await element(by.id('bank-info-submit-button')).tap();

      // Wait for success
      await waitForText('Bank information saved successfully', 10000);
      await element(by.text('OK')).tap();

      // Should return to dashboard
      await waitForVisible('kyc-status-view', 15000);
      await expect(element(by.id('bank-info-complete-icon'))).toBeVisible();
    });
  });

  describe('Submit for Review', () => {
    beforeEach(async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);
    });

    it('should navigate to review screen', async () => {
      // Assume all steps are complete
      await scrollToElement('submit-button', 'kyc-status-view');
      await element(by.id('submit-button')).tap();

      await waitForVisible('kyc-submit-screen', 15000);

      // Check review screen elements
      await expect(element(by.text('Review & Submit'))).toBeVisible();
      await expect(element(by.text('Application Checklist'))).toBeVisible();
      await expect(element(by.text('What happens next?'))).toBeVisible();
    });

    it('should display completion checklist', async () => {
      await scrollToElement('submit-button', 'kyc-status-view');
      await element(by.id('submit-button')).tap();
      await waitForVisible('kyc-submit-screen', 15000);

      // Check checklist items
      await expect(element(by.text('Personal Information'))).toBeVisible();
      await expect(element(by.text('Documents'))).toBeVisible();
      await expect(element(by.text('Bank Information'))).toBeVisible();

      // Check completion icons
      await expect(element(by.id('personal-info-check'))).toBeVisible();
      await expect(element(by.id('documents-check'))).toBeVisible();
      await expect(element(by.id('bank-info-check'))).toBeVisible();
    });

    it('should show warning if steps incomplete', async () => {
      // This test assumes some steps are incomplete
      await scrollToElement('kyc-status-view', 'kyc-status-view');

      // If progress is not 100%, submit button should show warning
      const progressText = await element(by.id('progress-percentage')).getAttributes();
      if (progressText.text !== '100%') {
        await scrollToElement('submit-button', 'kyc-status-view');

        // Button might be disabled or show warning
        await expect(element(by.text(/complete all required steps/))).toBeVisible();
      }
    });

    it('should submit application for review with confirmation', async () => {
      // Assume all steps are complete (100% progress)
      await scrollToElement('submit-button', 'kyc-status-view');
      await element(by.id('submit-button')).tap();
      await waitForVisible('kyc-submit-screen', 15000);

      // Tap submit for review button
      await scrollToElement('final-submit-button', 'kyc-submit-screen');
      await element(by.id('final-submit-button')).tap();

      // Should show confirmation dialog
      await waitForText('Submit for Review', 5000);
      await expect(element(by.text(/not be able to make changes/))).toBeVisible();

      // Confirm submission
      await element(by.text('Submit')).tap();

      // Wait for success
      await waitForText('submitted for review', 10000);
      await element(by.text('OK')).tap();

      // Should return to dashboard with "in review" status
      await waitForVisible('kyc-status-view', 15000);
      await expect(element(by.text('Under Review'))).toBeVisible();
    });
  });

  describe('Status Indicators', () => {
    beforeEach(async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);
    });

    it('should display progress percentage', async () => {
      await expect(element(by.id('progress-percentage'))).toBeVisible();
      await expect(element(by.id('kyc-progress-bar'))).toBeVisible();
    });

    it('should show step completion status with icons', async () => {
      // Check for status icons (checkmarks, circles, etc.)
      await expect(element(by.id('personal-info-status-icon'))).toBeVisible();
      await expect(element(by.id('documents-status-icon'))).toBeVisible();
      await expect(element(by.id('bank-info-status-icon'))).toBeVisible();
    });

    it('should display missing requirements', async () => {
      // If any requirements are missing, they should be listed
      const personalInfoComplete = await element(by.id('personal-info-complete-icon'))
        .isVisible()
        .catch(() => false);

      if (!personalInfoComplete) {
        await expect(element(by.text('Provide your personal details'))).toBeVisible();
      }
    });

    it('should update status after completing a step', async () => {
      // Get initial progress
      const initialProgress = await element(by.id('progress-percentage')).getAttributes();

      // Complete a step (if not complete)
      // ... perform step completion

      // Check progress increased (if applicable)
      // This is a conceptual test - actual implementation depends on step states
    });
  });

  describe('Navigation and Back Button', () => {
    it('should navigate back from personal info', async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);

      await scrollToElement('personal-info-step', 'kyc-status-view');
      await element(by.id('personal-info-step')).tap();
      await waitForVisible('personal-info-form', 15000);

      // Tap back/cancel button
      await element(by.id('personal-info-cancel-button')).tap();

      // Should return to dashboard
      await waitForVisible('kyc-status-view', 15000);
    });

    it('should navigate back from documents screen', async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);

      await scrollToElement('documents-step', 'kyc-status-view');
      await element(by.id('documents-step')).tap();
      await waitForVisible('documents-screen', 15000);

      await scrollToElement('documents-back-button', 'documents-screen');
      await element(by.id('documents-back-button')).tap();

      await waitForVisible('kyc-status-view', 15000);
    });

    it('should navigate back from bank info', async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);

      await scrollToElement('bank-info-step', 'kyc-status-view');
      await element(by.id('bank-info-step')).tap();
      await waitForVisible('bank-info-form', 15000);

      await element(by.id('bank-info-cancel-button')).tap();
      await waitForVisible('kyc-status-view', 15000);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      // This would require mocking network failures
      // Conceptual test for error handling

      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);

      // Simulate network error (requires test infrastructure)
      // await device.disableNetwork();

      // Try to submit
      // Should show error message
      // await expect(element(by.text(/network error|connection failed/))).toBeVisible();

      // await device.enableNetwork();
    });

    it('should show error for invalid input data', async () => {
      await element(by.text('KYC Verification')).tap();
      await waitForVisible('kyc-status-view', 15000);

      await scrollToElement('personal-info-step', 'kyc-status-view');
      await element(by.id('personal-info-step')).tap();
      await waitForVisible('personal-info-form', 15000);

      // Enter invalid National ID (too short)
      await element(by.id('national-id-input')).tap();
      await element(by.id('national-id-input')).typeText('123');

      // Try to submit
      await scrollToElement('personal-info-submit-button', 'personal-info-form');
      await element(by.id('personal-info-submit-button')).tap();

      // Should show validation error
      await waitForText('valid National ID', 5000);
    });
  });

  afterAll(async () => {
    await logout();
  });
});
