// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import fetchMock from 'jest-fetch-mock';

window.HTMLElement.prototype.scrollIntoView = function() {};

fetchMock.enableMocks();

beforeAll(() => {
  const localStorageMock = (() => {
    let store = {};
    return {
      getItem(key) {
        return store[key] || null;
      },
      setItem(key, value) {
        store[key] = value.toString();
      },
      removeItem(key) {
        delete store[key];
      },
      clear() {
        store = {};
      },
    };
  })();
  Object.defineProperty(window, 'localStorage', { value: localStorageMock });
});

beforeEach(() => {
  fetchMock.resetMocks();
});