from playwright.sync_api import Page
from helpers import BASE

def test_service_worker_clears_old_caches(page: Page):
    # Abort sw.js loads during initial navigation to prevent auto-registration
    page.route("**/sw.js", lambda route: route.abort())
    page.goto(BASE, wait_until="networkidle")

    # Clear any existing service workers that might be lingering
    page.evaluate('''() => {
        return navigator.serviceWorker.getRegistrations().then(registrations => {
            return Promise.all(registrations.map(r => r.unregister()));
        });
    }''')

    # Unroute so we can manually register later
    page.unroute("**/sw.js")

    # Manually create old caches
    page.evaluate('''() => {
        return Promise.all([
            caches.open('datadashboard-v1').then(c => c.put('/', new Response('v1'))),
            caches.open('datadashboard-v2').then(c => c.put('/', new Response('v2')))
        ]);
    }''')

    # Verify they are present
    keys = page.evaluate('() => caches.keys()')
    assert 'datadashboard-v1' in keys
    assert 'datadashboard-v2' in keys

    # Register the service worker
    page.evaluate('''() => {
        return navigator.serviceWorker.register('/sw.js').then(reg => {
            return new Promise(resolve => {
                const sw = reg.installing || reg.waiting || reg.active;
                if (sw.state === 'activated') {
                    resolve();
                } else {
                    sw.addEventListener('statechange', e => {
                        if (e.target.state === 'activated') {
                            resolve();
                        }
                    });
                }
            });
        });
    }''')

    # The activate event deletes old caches. Wait a bit for the promise chain.
    page.wait_for_timeout(1000)

    final_keys = page.evaluate('() => caches.keys()')
    assert 'datadashboard-v1' not in final_keys
    assert 'datadashboard-v2' not in final_keys

    # Check that there is at least one datadashboard cache remaining
    assert any('datadashboard' in k for k in final_keys), f"Expected a cache, got {final_keys}"
