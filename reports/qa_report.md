# 🤖 QAgent — Frontend QA Report
**Generated:** 2026-04-03 20:54

## ❌ Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | 6 |
| ✅ Passed | 0 |
| ❌ Failed | 6 |
| Pass Rate | 0% |

## 🐛 Bug Reports

### 🔴 CRITICAL (3)

#### BUG-001: Timeouts and 404 Error on Login and Checkout

- **Test Case:** `TC001`
- **Expected:** User is logged in and can complete checkout
- **Actual:** The test failed due to multiple timeouts and a 404 error, indicating issues with page loading and element interaction
- **Screenshot:** `reports/screenshots/tc001_result.png`

**Steps to Reproduce:**
1. `navigate: https://qagent-iota.vercel.app/`
2. `type: #user-name | standard_user`
3. `type: #password | secret_sauce`
4. `click: #login-button`
5. `assert_url_contains: inventory`
6. `click: #add-to-cart-sauce-labs-backpack`
7. `click: #shopping-cart-container`
8. `assert_text: #cart-quantity | 1`
9. `click: #checkout`
10. `type: #first-name | John`
11. `type: #last-name | Doe`
12. `type: #postal-code | 12345`
13. `click: #continue`
14. `assert_text: #checkout-complete | THANK YOU FOR YOUR ORDER`

#### BUG-005: Timeouts and failed assertions in filter by category test

- **Test Case:** `TC005`
- **Expected:** User can filter by category and navigate to about page
- **Actual:** The test failed due to multiple timeouts and failed assertions throughout the test case execution
- **Screenshot:** `reports/screenshots/tc005_result.png`

**Steps to Reproduce:**
1. `navigate: https://qagent-iota.vercel.app/`
2. `type: #user-name | standard_user`
3. `type: #password | secret_sauce`
4. `click: #login-button`
5. `assert_url_contains: inventory`
6. `click: #item_4_title_link`
7. `assert_text: #item_4_title | Sauce Labs Backpack`
8. `click: #react-burger-menu-btn`
9. `click: #about_sidebar_link`
10. `assert_url_contains: about`

#### BUG-006: Timeouts and Element Locator Issues

- **Test Case:** `TC006`
- **Expected:** User can add to cart and view cart
- **Actual:** The test failed due to timeouts and inability to locate elements on the page, resulting in failed assertions
- **Screenshot:** `reports/screenshots/tc006_result.png`

**Steps to Reproduce:**
1. `navigate: https://qagent-iota.vercel.app/`
2. `type: #user-name | standard_user`
3. `type: #password | secret_sauce`
4. `click: #login-button`
5. `assert_url_contains: inventory`
6. `click: #add-to-cart-sauce-labs-backpack`
7. `click: #shopping-cart-container`
8. `assert_text: #cart-quantity | 1`
9. `assert_text: #item_0_title | Sauce Labs Backpack`

### 🟠 HIGH (3)

#### BUG-002: Element Locator Timeout

- **Test Case:** `TC002`
- **Expected:** Error message is displayed for invalid credentials
- **Actual:** The test failed due to timeouts and inability to locate elements on the page, resulting in an assertion failure
- **Screenshot:** `reports/screenshots/tc002_result.png`

**Steps to Reproduce:**
1. `navigate: https://qagent-iota.vercel.app/`
2. `type: #user-name | wrong_user`
3. `type: #password | wrong_pass`
4. `click: #login-button`
5. `assert_text: #login-button | Epic sadface: Username and password do not match any user in this service`

#### BUG-003: Timeout Error on Locked User Test

- **Test Case:** `TC003`
- **Expected:** Error message is displayed for locked user
- **Actual:** The test failed due to a timeout error when trying to locate and interact with elements on the page, resulting in a failed assertion
- **Screenshot:** `reports/screenshots/tc003_result.png`

**Steps to Reproduce:**
1. `navigate: https://qagent-iota.vercel.app/`
2. `type: #user-name | locked_user`
3. `type: #password | secret_sauce`
4. `click: #login-button`
5. `assert_text: #login-button | Epic sadface: Sorry, this user has been locked out.`

#### BUG-004: Login Button Timeout Error

- **Test Case:** `TC004`
- **Expected:** Error message is displayed for empty input
- **Actual:** The test failed due to a timeout error when attempting to click and assert the login button
- **Screenshot:** `reports/screenshots/tc004_result.png`

**Steps to Reproduce:**
1. `navigate: https://qagent-iota.vercel.app/`
2. `click: #login-button`
3. `assert_text: #login-button | Epic sadface: Username is required`
