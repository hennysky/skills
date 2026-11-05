;(() => {
  const contents = document.querySelector('.planning-contents');
  if (!contents) return;
  const narrow = matchMedia('(max-width:900px)');
  const adapt = () => { contents.open = !narrow.matches; };
  adapt(); narrow.addEventListener('change',adapt);
  const links = [...contents.querySelectorAll('a[href^="#"]')];
  const sections = links.map(link=>document.getElementById(decodeURIComponent(link.hash.slice(1)))) .filter(Boolean);
  const updateCurrent = () => {
    const atEnd = scrollY + innerHeight >= document.documentElement.scrollHeight - 2;
    const current = atEnd ? sections.at(-1) : sections.filter(section=>section.getBoundingClientRect().top <= 140).at(-1) || sections[0];
    for (const link of links) {
      if (link.hash === '#' + current?.id) link.setAttribute('aria-current','location');
      else link.removeAttribute('aria-current');
    }
  };
  let frame;
  addEventListener('scroll',()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(updateCurrent);},{passive:true});
  addEventListener('resize',updateCurrent);
  links.forEach(link=>link.addEventListener('click',()=>{if(narrow.matches)contents.open=false;}));
  // A return link must expose the compact mobile directory, even when its anchor did not change.
  const exposeContents = () => { if(location.hash === '#planning-nav')contents.open=true; };
  addEventListener('hashchange',exposeContents);
  document.querySelectorAll('a[href="#planning-nav"]').forEach(link=>link.addEventListener('click',()=>{contents.open=true;}));
  exposeContents(); updateCurrent();
  const boxes = [...document.querySelectorAll('.checklist input')];
  const updateProgress = () => {
    const complete=boxes.filter(box=>box.checked).length;
    const output=document.querySelector('[data-plan-progress]'),progress=document.querySelector('.planning-progress progress');
    if(output)output.textContent=`${complete} / ${boxes.length}`;
    if(progress)progress.value=complete;
  };
  boxes.forEach(box=>box.addEventListener('change',updateProgress));updateProgress();
})();
