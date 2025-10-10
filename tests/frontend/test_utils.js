/**
 * Utilidades de Testing para Frontend Citrino
 * Proporciona funciones helper para tests manuales y automáticos
 */

class TestUtils {
    constructor() {
        this.testResults = [];
        this.currentSuite = null;
        this.verbose = true;
    }

    /**
     * Inicializa una suite de tests
     */
    describe(suiteName, callback) {
        this.currentSuite = {
            name: suiteName,
            tests: [],
            startTime: Date.now()
        };

        if (this.verbose) {
            console.log(`📋 Suite: ${suiteName}`);
        }

        callback();
        this.runSuite();
    }

    /**
     * Define un test individual
     */
    it(testName, testFunction) {
        if (!this.currentSuite) {
            throw new Error('Test debe estar dentro de una suite (describe)');
        }

        this.currentSuite.tests.push({
            name: testName,
            function: testFunction,
            status: 'pending'
        });
    }

    /**
     * Ejecuta todos los tests de la suite actual
     */
    async runSuite() {
        const suite = this.currentSuite;
        let passedTests = 0;
        let failedTests = 0;

        console.log(`\n🚀 Ejecutando ${suite.tests.length} tests en "${suite.name}"...`);

        for (const test of suite.tests) {
            try {
                const startTime = Date.now();
                await test.function();
                const duration = Date.now() - startTime;

                test.status = 'passed';
                test.duration = duration;
                passedTests++;

                console.log(`  ✅ ${test.name} (${duration}ms)`);

            } catch (error) {
                test.status = 'failed';
                test.error = error.message;
                failedTests++;

                console.log(`  ❌ ${test.name}`);
                console.log(`     Error: ${error.message}`);
            }
        }

        const totalDuration = Date.now() - suite.startTime;
        const suiteResult = {
            name: suite.name,
            total: suite.tests.length,
            passed: passedTests,
            failed: failedTests,
            duration: totalDuration,
            tests: suite.tests
        };

        this.testResults.push(suiteResult);
        this.printSuiteSummary(suiteResult);
        return suiteResult;
    }

    /**
     * Imprime resumen de la suite
     */
    printSuiteSummary(suite) {
        const status = suite.failed === 0 ? '✅ PASSED' : '❌ FAILED';
        console.log(`\n${status} ${suite.name}: ${suite.passed}/${suite.total} passed (${suite.duration}ms)`);
    }

    /**
     * Función assert para validaciones
     */
    assert(condition, message = 'Assertion failed') {
        if (!condition) {
            throw new Error(message);
        }
    }

    /**
     * Assert equals
     */
    assertEqual(actual, expected, message) {
        this.assert(actual === expected,
            message || `Expected ${expected}, but got ${actual}`);
    }

    /**
     * Assert not equals
     */
    assertNotEqual(actual, expected, message) {
        this.assert(actual !== expected,
            message || `Expected not ${expected}, but got ${actual}`);
    }

    /**
     * Assert contains
     */
    assertContains(haystack, needle, message) {
        const contains = haystack.includes && haystack.includes(needle);
        this.assert(contains,
            message || `Expected "${haystack}" to contain "${needle}"`);
    }

    /**
     * Assert array length
     */
    assertLength(array, expectedLength, message) {
        this.assertEqual(array.length, expectedLength,
            message || `Expected array length ${expectedLength}, but got ${array.length}`);
    }

    /**
     * Assert element exists
     */
    assertElementExists(selector, context = document) {
        const element = context.querySelector(selector);
        this.assert(element, `Element with selector "${selector}" should exist`);
        return element;
    }

    /**
     * Assert element visible
     */
    assertElementVisible(selector, context = document) {
        const element = this.assertElementExists(selector, context);
        const styles = window.getComputedStyle(element);
        this.assert(styles.display !== 'none' && styles.visibility !== 'hidden',
            `Element "${selector}" should be visible`);
        return element;
    }

    /**
     * Assert element hidden
     */
    assertElementHidden(selector, context = document) {
        const element = this.assertElementExists(selector, context);
        const styles = window.getComputedStyle(element);
        this.assert(styles.display === 'none' || styles.visibility === 'hidden',
            `Element "${selector}" should be hidden`);
        return element;
    }

    /**
     * Simula click en elemento
     */
    async click(selector, context = document) {
        const element = this.assertElementExists(selector, context);
        element.click();
        await this.waitFor(50); // Pequeña espera para eventos
        return element;
    }

    /**
     * Simula input en formulario
     */
    async type(selector, text, context = document) {
        const element = this.assertElementExists(selector, context);
        element.value = text;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        await this.waitFor(50);
        return element;
    }

    /**
     * Espera un tiempo determinado
     */
    async waitFor(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Espera a que un elemento aparezca
     */
    async waitForElement(selector, timeout = 5000, context = document) {
        const startTime = Date.now();
        while (Date.now() - startTime < timeout) {
            const element = context.querySelector(selector);
            if (element) return element;
            await this.waitFor(100);
        }
        throw new Error(`Element "${selector}" not found within ${timeout}ms`);
    }

    /**
     * Mock de API responses
     */
    mockAPI(endpoint, response, delay = 100) {
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            if (url.includes(endpoint)) {
                return new Promise(resolve => {
                    setTimeout(() => {
                        resolve({
                            ok: true,
                            json: () => Promise.resolve(response),
                            text: () => Promise.resolve(JSON.stringify(response))
                        });
                    }, delay);
                });
            }
            return originalFetch.apply(this, arguments);
        };
    }

    /**
     * Restaura fetch original
     */
    restoreAPI() {
        window.fetch = this.originalFetch;
    }

    /**
     * Limpia localStorage
     */
    clearStorage() {
        localStorage.clear();
        sessionStorage.clear();
    }

    /**
     * Genera reporte HTML
     */
    generateHTMLReport() {
        const totalSuites = this.testResults.length;
        const totalTests = this.testResults.reduce((sum, suite) => sum + suite.total, 0);
        const totalPassed = this.testResults.reduce((sum, suite) => sum + suite.passed, 0);
        const totalFailed = this.testResults.reduce((sum, suite) => sum + suite.failed, 0);
        const totalDuration = this.testResults.reduce((sum, suite) => sum + suite.duration, 0);

        const reportHTML = `
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Citrino Frontend Test Report</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    .test-passed { color: #28a745; }
                    .test-failed { color: #dc3545; }
                    .test-suite { margin-bottom: 2rem; }
                    .test-details { font-family: monospace; font-size: 0.9rem; }
                </style>
            </head>
            <body>
                <div class="container py-4">
                    <h1>🧪 Citrino Frontend Test Report</h1>
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h3 class="test-passed">${totalPassed}</h3>
                                    <p class="mb-0">Passed</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h3 class="test-failed">${totalFailed}</h3>
                                    <p class="mb-0">Failed</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h3>${totalTests}</h3>
                                    <p class="mb-0">Total Tests</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h3>${totalDuration}ms</h3>
                                    <p class="mb-0">Duration</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    ${this.testResults.map(suite => this.generateSuiteHTML(suite)).join('')}
                </div>
            </body>
            </html>
        `;

        return reportHTML;
    }

    /**
     * Genera HTML para una suite
     */
    generateSuiteHTML(suite) {
        const statusIcon = suite.failed === 0 ? '✅' : '❌';
        return `
            <div class="test-suite card">
                <div class="card-header">
                    <h4>${statusIcon} ${suite.name}</h4>
                    <small class="text-muted">${suite.passed}/${suite.total} passed (${suite.duration}ms)</small>
                </div>
                <div class="card-body">
                    ${suite.tests.map(test => `
                        <div class="row mb-2">
                            <div class="col-md-8">
                                <span class="${test.status === 'passed' ? 'test-passed' : 'test-failed'}">
                                    ${test.status === 'passed' ? '✅' : '❌'} ${test.name}
                                </span>
                            </div>
                            <div class="col-md-4 text-end">
                                <small class="text-muted">${test.duration || 0}ms</small>
                            </div>
                            ${test.error ? `<div class="col-12 test-details text-danger">${test.error}</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Exporta resultados como JSON
     */
    exportResults() {
        const results = {
            timestamp: new Date().toISOString(),
            summary: {
                totalSuites: this.testResults.length,
                totalTests: this.testResults.reduce((sum, suite) => sum + suite.total, 0),
                totalPassed: this.testResults.reduce((sum, suite) => sum + suite.passed, 0),
                totalFailed: this.testResults.reduce((sum, suite) => sum + suite.failed, 0),
                totalDuration: this.testResults.reduce((sum, suite) => sum + suite.duration, 0)
            },
            suites: this.testResults
        };

        const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `citrino-test-results-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);

        return results;
    }

    /**
     * Resetea todos los resultados
     */
    reset() {
        this.testResults = [];
        this.currentSuite = null;
    }
}

// Exportar globalmente para uso en tests
window.TestUtils = TestUtils;
window.describe = function(name, callback) {
    if (!window.testRunner) {
        window.testRunner = new TestUtils();
    }
    return window.testRunner.describe(name, callback);
};

window.it = function(name, testFunction) {
    if (!window.testRunner) {
        throw new Error('it() must be called within describe()');
    }
    return window.testRunner.it(name, testFunction);
};