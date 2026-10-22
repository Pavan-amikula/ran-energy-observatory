"""Browser interaction verification and a real screen recording of the app."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def main():
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        context=browser.new_context(viewport={'width':1600,'height':1200},device_scale_factor=1,
            record_video_dir=str(ROOT/'work'/'video'),record_video_size={'width':1600,'height':1200})
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8000')
        page.wait_for_function("document.getElementById('status').textContent.includes('complete')")
        page.screenshot(path=str(ROOT/'results'/'dashboard.png'),full_page=True)
        page.wait_for_timeout(2200)
        page.locator('[data-policy="always_on"]').click();page.wait_for_timeout(2200)
        page.locator('[data-policy="micro_sleep"]').click();page.wait_for_timeout(2200)
        page.locator('[data-policy="compact"]').click()
        page.locator('#play').click();page.wait_for_timeout(4000);page.locator('#play').click()
        page.locator('#scrub').fill('40');page.locator('#scrub').dispatch_event('input');page.wait_for_timeout(2000)
        page.locator('#radio').select_option('LTE');page.locator('#run').click()
        page.wait_for_function("document.getElementById('meta').textContent.includes('100 PRBs')")
        page.wait_for_timeout(2500);page.screenshot(path=str(ROOT/'results'/'lte-dashboard.png'),full_page=True)
        page.locator('#radio').select_option('NR');page.locator('#scenario').select_option('overload')
        page.locator('#load').fill('90');page.locator('#load').dispatch_event('input');page.locator('#run').click()
        page.wait_for_function("document.getElementById('status').textContent.includes('complete')")
        page.wait_for_timeout(2500)
        page.locator('#trace').set_input_files(str(ROOT/'data'/'example_packets.csv'))
        page.wait_for_function("document.getElementById('status').textContent.includes('Imported')")
        assert '11/' in page.locator('#delivered').inner_text()
        with page.expect_download() as download:page.locator('#export').click()
        saved=ROOT/'work'/'download.json';download.value.save_as(saved)
        assert json.loads(saved.read_text())['meta']['source'].startswith('user-imported')
        page.locator('#live').click();page.wait_for_timeout(1200)
        assert 'Connected' in page.locator('#liveStatus').inner_text()
        page.locator('#live').click()
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(1500)
        page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(300)
        page.screenshot(path=str(ROOT/'results'/'mobile-dashboard.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        video=page.video
        context.close();video.save_as(str(ROOT/'work'/'demo.webm'));browser.close()
    (ROOT/'results'/'browser-validation.json').write_text(json.dumps({'page_errors':errors,'checks':['NR initial result','three policy tabs','animated replay','time scrubbing','LTE geometry','overload experiment','CSV upload','JSON export','telemetry connection','390px responsive layout']},indent=2))
    assert not errors,errors
    print('Browser checks passed; real app recording saved to work/demo.webm')

if __name__=='__main__':main()
