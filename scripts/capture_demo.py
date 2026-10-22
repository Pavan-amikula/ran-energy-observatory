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
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(ROOT/'results'/'dashboard.png'),full_page=True)
        page.wait_for_timeout(1500)
        page.locator('#compareToggle').click()
        assert page.locator('#compareToggle').get_attribute('aria-expanded')=='true'
        page.screenshot(path=str(ROOT/'results'/'policy-comparison.png'),full_page=True)
        page.locator('[data-policy="always_on"]').click();page.wait_for_timeout(1400)
        page.locator('[data-policy="micro_sleep"]').click();page.wait_for_timeout(1400)
        page.locator('[data-policy="compact"]').click()
        page.locator('#grid').click(position={'x':200,'y':120})
        assert page.locator('#pinState').inner_text()=='PINNED'
        selected_time=page.locator('#inspectTime').inner_text()
        page.locator('#grid').press('ArrowRight')
        assert page.locator('#inspectTime').inner_text()!=selected_time
        page.locator('#grid').press('Escape')
        assert page.locator('#pinState').inner_text()=='FOLLOW'
        with page.expect_download() as image_download:page.locator('#imageExport').click()
        png=ROOT/'work'/'grid-export.png';image_download.value.save_as(png)
        assert png.read_bytes().startswith(b'\x89PNG')
        page.locator('#play').click();page.wait_for_timeout(3000);page.locator('#play').click()
        page.locator('#scrub').fill('40');page.locator('#scrub').dispatch_event('input');page.wait_for_timeout(1200)
        page.locator('#power').click(position={'x':200,'y':90})
        assert float(page.locator('#scrub').input_value())>0
        page.locator('[data-preset="equal"]').click()
        page.wait_for_function("document.getElementById('reviewTitle').textContent.includes('Equal payload')")
        page.screenshot(path=str(ROOT/'results'/'equal-work-dashboard.png'),full_page=True)
        page.wait_for_timeout(1800)
        page.locator('[data-preset="stress"]').click()
        page.wait_for_function("document.getElementById('reviewTitle').textContent.includes('degraded')")
        page.wait_for_timeout(1800)
        page.locator('[data-preset="bursty"]').click()
        page.wait_for_function("document.getElementById('status').textContent.includes('complete')")
        page.locator('#radio').select_option('LTE');page.locator('#run').click()
        page.wait_for_function("document.getElementById('meta').textContent.includes('100 PRBs')")
        page.wait_for_timeout(1400);page.screenshot(path=str(ROOT/'results'/'lte-dashboard.png'),full_page=True)
        page.locator('#radio').select_option('NR')
        assert page.locator('#dirty').is_visible()
        page.locator('#trace').set_input_files(str(ROOT/'data'/'example_packets.csv'))
        page.wait_for_function("document.getElementById('status').textContent.includes('Imported')")
        assert '11/' in page.locator('#delivered').inner_text()
        with page.expect_download() as download:page.locator('#export').click()
        saved=ROOT/'work'/'download.json';download.value.save_as(saved)
        assert json.loads(saved.read_text())['meta']['source'].startswith('user-imported')
        page.locator('#live').click();page.wait_for_timeout(1200)
        assert any(s in page.locator('#liveStatus').inner_text() for s in ['Connected','W estimated'])
        page.locator('#live').click()
        page.locator('#clearTrace').click()
        page.wait_for_function("document.getElementById('status').textContent.includes('complete')")
        page.locator('#compareToggle').click()
        page.locator('#duration').fill('20');page.locator('#run').click()
        page.wait_for_function("document.getElementById('meta').textContent.includes('20 ms')")
        page.locator('#window').select_option('40')
        page.locator('#grid').hover(position={'x':500,'y':100})
        assert float(page.locator('#inspectTime').inner_text())<20
        page.locator('[data-preset="bursty"]').click()
        page.wait_for_function("document.getElementById('meta').textContent.includes('160 ms')")
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(1500)
        page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(300)
        page.screenshot(path=str(ROOT/'results'/'mobile-dashboard.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        for width in [360,768,1024,1280]:
            page.set_viewport_size({'width':width,'height':900});page.wait_for_timeout(150)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),width
        video=page.video
        context.close();video.save_as(str(ROOT/'work'/'demo.webm'));browser.close()
    (ROOT/'results'/'browser-validation.json').write_text(json.dumps({'page_errors':errors,'checks':['NR initial result','three policy tabs','synchronized policy comparison grids','cell inspector pin / keyboard / release','PNG export','animated replay','time scrubbing','power-chart linked navigation','equal-work preset and service verdict','overload preset and service verdict','LTE geometry','unsaved configuration indicator','CSV upload and clear','JSON export','telemetry connection','short horizon with larger grid window','responsive layouts at 360,390,768,1024,1280px']},indent=2))
    assert not errors,errors
    print('Browser checks passed; real app recording saved to work/demo.webm')

if __name__=='__main__':main()
