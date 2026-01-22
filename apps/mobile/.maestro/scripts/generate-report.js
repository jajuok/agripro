const PDFDocument = require('pdfkit');
const fs = require('fs');

// Test results from the complete E2E flow
const testResults = {
  suiteName: 'AgriScheme Pro - Complete E2E Test Suite',
  runDate: new Date().toISOString(),
  platform: 'iPhone 16 Pro - iOS 18.4',
  totalDuration: '~2 minutes',
  testCases: [
    {
      id: 'TC-001',
      section: 'Setup',
      title: 'Clear app state and handle logged-in state',
      status: 'Passed',
      steps: [
        { step: 'Launch app with clear state', expected: 'App launches', result: 'COMPLETED' },
        { step: 'Logout if already logged in', expected: 'Logout successful', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-002',
      section: 'Registration',
      title: 'Register new user account',
      status: 'Passed',
      steps: [
        { step: 'Verify login screen displays', expected: '"Farm Management System" visible', result: 'COMPLETED' },
        { step: 'Navigate to registration', expected: '"Create Account" visible', result: 'COMPLETED' },
        { step: 'Fill first name', expected: 'Input accepted', result: 'COMPLETED' },
        { step: 'Fill last name', expected: 'Input accepted', result: 'COMPLETED' },
        { step: 'Fill email (unique)', expected: 'Input accepted', result: 'COMPLETED' },
        { step: 'Fill phone number', expected: 'Input accepted', result: 'COMPLETED' },
        { step: 'Fill password', expected: 'Input accepted', result: 'COMPLETED' },
        { step: 'Fill confirm password', expected: 'Input accepted', result: 'COMPLETED' },
        { step: 'Submit registration', expected: 'Account created', result: 'COMPLETED' },
        { step: 'Verify home screen', expected: '"Welcome back!" visible', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-003',
      section: 'Authentication',
      title: 'Logout after registration',
      status: 'Passed',
      steps: [
        { step: 'Navigate to profile tab', expected: 'Profile screen visible', result: 'COMPLETED' },
        { step: 'Tap logout button', expected: 'User logged out', result: 'COMPLETED' },
        { step: 'Verify login screen', expected: '"Farm Management System" visible', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-004',
      section: 'Authentication',
      title: 'Login with newly created account',
      status: 'Passed',
      steps: [
        { step: 'Enter email', expected: 'Email input accepted', result: 'COMPLETED' },
        { step: 'Enter password', expected: 'Password input accepted', result: 'COMPLETED' },
        { step: 'Tap login button', expected: 'Login successful', result: 'COMPLETED' },
        { step: 'Verify home screen', expected: '"Welcome back!" visible', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-005',
      section: 'Home Screen',
      title: 'Verify home screen elements',
      status: 'Passed',
      steps: [
        { step: 'Check farm overview', expected: '"Here\'s your farm overview" visible', result: 'COMPLETED' },
        { step: 'Check quick actions', expected: '"Quick Actions" visible', result: 'COMPLETED' },
        { step: 'Check KYC status', expected: '"KYC Status" visible', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-006',
      section: 'Navigation',
      title: 'Farms tab navigation and content',
      status: 'Passed',
      steps: [
        { step: 'Navigate to Farms tab', expected: 'Farms screen visible', result: 'COMPLETED' },
        { step: 'Verify empty state', expected: '"No Farms Yet" visible', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-007',
      section: 'Navigation',
      title: 'Tasks tab navigation and content',
      status: 'Passed',
      steps: [
        { step: 'Navigate to Tasks tab', expected: 'Tasks screen visible', result: 'COMPLETED' },
        { step: 'Verify tasks content', expected: '"Today" visible', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-008',
      section: 'Navigation',
      title: 'Market tab navigation and content',
      status: 'Passed',
      steps: [
        { step: 'Navigate to Market tab', expected: 'Market screen visible', result: 'COMPLETED' },
        { step: 'Verify market content', expected: '"Market Prices" visible', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-009',
      section: 'Profile',
      title: 'Profile tab navigation and content',
      status: 'Passed',
      steps: [
        { step: 'Navigate to Profile tab', expected: 'Profile screen visible', result: 'COMPLETED' },
        { step: 'Verify KYC badge', expected: '"KYC Verified" visible', result: 'COMPLETED' },
        { step: 'Verify stats - Farms', expected: '"Farms" visible', result: 'COMPLETED' },
        { step: 'Verify stats - Hectares', expected: '"Hectares" visible', result: 'COMPLETED' }
      ]
    },
    {
      id: 'TC-010',
      section: 'Authentication',
      title: 'Final logout',
      status: 'Passed',
      steps: [
        { step: 'Tap logout button', expected: 'User logged out', result: 'COMPLETED' },
        { step: 'Verify login screen', expected: '"Farm Management System" visible', result: 'COMPLETED' },
        { step: 'Verify app title', expected: '"AgriScheme Pro" visible', result: 'COMPLETED' },
        { step: 'Verify login button', expected: '"Login" visible', result: 'COMPLETED' }
      ]
    }
  ]
};

// Calculate summary
const passed = testResults.testCases.filter(tc => tc.status === 'Passed').length;
const failed = testResults.testCases.filter(tc => tc.status === 'Failed').length;
const total = testResults.testCases.length;

// Create PDF
const doc = new PDFDocument({ margin: 50 });
const outputPath = '/Users/oscarrombo/agripro/apps/mobile/test-reports/testrail-report.pdf';

// Ensure directory exists
const reportDir = '/Users/oscarrombo/agripro/apps/mobile/test-reports';
if (!fs.existsSync(reportDir)) {
  fs.mkdirSync(reportDir, { recursive: true });
}

doc.pipe(fs.createWriteStream(outputPath));

// Title
doc.fontSize(24).font('Helvetica-Bold').text('TestRail Test Execution Report', { align: 'center' });
doc.moveDown();

// Suite info
doc.fontSize(12).font('Helvetica');
doc.text(`Suite: ${testResults.suiteName}`);
doc.text(`Run Date: ${new Date().toLocaleDateString('en-US', {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit'
})}`);
doc.text(`Platform: ${testResults.platform}`);
doc.text(`Duration: ${testResults.totalDuration}`);
doc.moveDown();

// Summary box
doc.rect(50, doc.y, 500, 60).stroke();
const summaryY = doc.y + 10;
doc.fontSize(14).font('Helvetica-Bold').text('Test Summary', 60, summaryY);
doc.fontSize(12).font('Helvetica');
doc.text(`Total Test Cases: ${total}`, 60, summaryY + 20);
doc.fillColor('green').text(`Passed: ${passed}`, 200, summaryY + 20);
doc.fillColor('red').text(`Failed: ${failed}`, 300, summaryY + 20);
doc.fillColor('black').text(`Pass Rate: ${((passed/total)*100).toFixed(1)}%`, 400, summaryY + 20);
doc.y = summaryY + 50;
doc.moveDown(2);

// Test Cases
doc.fontSize(16).font('Helvetica-Bold').text('Test Case Details');
doc.moveDown();

testResults.testCases.forEach((tc, index) => {
  // Check if we need a new page
  if (doc.y > 650) {
    doc.addPage();
  }

  // Test case header
  doc.fontSize(12).font('Helvetica-Bold');
  const statusColor = tc.status === 'Passed' ? 'green' : 'red';
  doc.fillColor('black').text(`${tc.id}: ${tc.title}`, { continued: true });
  doc.fillColor(statusColor).text(` [${tc.status}]`);
  doc.fillColor('black');

  doc.fontSize(10).font('Helvetica').text(`Section: ${tc.section}`);
  doc.moveDown(0.5);

  // Steps table
  doc.fontSize(9);
  tc.steps.forEach((step, stepIndex) => {
    if (doc.y > 700) {
      doc.addPage();
    }
    doc.text(`  ${stepIndex + 1}. ${step.step}`);
    doc.text(`     Expected: ${step.expected} | Result: ${step.result}`, { indent: 20 });
  });

  doc.moveDown();
});

// Footer
doc.fontSize(10).font('Helvetica-Oblique');
doc.text('Generated by Maestro E2E Testing Framework', 50, 750, { align: 'center' });

doc.end();

console.log(`Report generated: ${outputPath}`);
