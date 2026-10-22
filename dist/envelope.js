(() => {
  'use strict';
  function init(root) {
    if (root.envelope) return;
    const get = name => root.querySelector(`[data-part="${name}"]`);
    const stage=root.querySelector('.es-stage'), frame=root.querySelector('.es-frame');
    const objects=root.querySelector('.es-objects');
    const flap=get('flap'), wrap=get('flap-wrap'), inner=flap.querySelector('.es-inner'), outer=flap.querySelector('.es-outer');
    const letter=get('letter'), seal=get('seal'), stamp=get('stamp'), flash=get('flash');
    const replay=get('replay'), pause=get('pause');
    pause.hidden=true;
    const reduced=matchMedia('(prefers-reduced-motion: reduce)'), mobile=matchMedia('(max-width: 600px)');
    let observer, started=false, disposed=false;
    function fit(){stage.style.transform=`scale(${frame.clientWidth/(mobile.matches?390:1280)})`;}
    const resize=new ResizeObserver(fit); resize.observe(frame); mobile.addEventListener('change',fit); fit();
    if (!window.gsap) {root.dataset.error='gsap-unavailable';replay.hidden=true;pause.hidden=true;return;}
    const g=window.gsap;
    function faces(){const open=g.getProperty(flap,'rotationX')>90;outer.style.opacity=open?'0':'1';inner.style.opacity=open?'1':'0';wrap.style.zIndex=open?'1':'4';}
    const particles=Array.from({length:24},()=>{const el=document.createElement('i');el.className='es-spark';objects.append(el);return el;});
    const tl=g.timeline({paused:true,onUpdate:faces,onComplete:()=>{pause.textContent='Пауза';pause.hidden=true;}});
    tl.set(flap,{rotationX:212,transformPerspective:900},0)
      .set(letter,{y:-105,rotation:-2,opacity:1},0)
      .set(seal,{opacity:0,scale:1,filter:'brightness(1)'},0)
      .set(stamp,{x:0,y:0,rotation:0,transformOrigin:'55px 154px'},0)
      .set(flash,{opacity:0,scale:.3},0)
      .set(get('env'),{y:0},0)
      .to(letter,{y:-119,duration:.7,ease:'sine.inOut'},0)
      .to(letter,{y:0,rotation:0,duration:1.7,ease:'power2.inOut'},.7)
      .to(flap,{rotationX:0,duration:.9,ease:'power2.inOut'},2.4)
      .to(stamp,{x:-118,y:101,rotation:-28,duration:.76,ease:'power2.inOut'},3)
      .to(stamp,{y:141,duration:.14,ease:'power3.in'},3.76)
      .set(seal,{opacity:1,scale:.94,filter:'brightness(1.7)'},3.9)
      .to(seal,{scale:1,filter:'brightness(1)',duration:.38,ease:'power2.out'},3.9)
      .to(flash,{opacity:.85,scale:1,duration:.10},3.9)
      .to(flash,{opacity:0,scale:1.5,duration:.65,ease:'power2.out'},4)
      .to(get('env'),{y:2,duration:.06,repeat:1,yoyo:true},3.9)
      .to(stamp,{x:0,y:0,rotation:0,duration:1,ease:'power2.inOut'},4.15);
    particles.forEach((el,i)=>{
      const angle=i*2.399963, distance=48+(i*37%108);
      tl.set(el,{x:0,y:0,scale:.6+(i%4)*.3,opacity:0},0)
        .set(el,{opacity:.95},3.9)
        .to(el,{x:Math.cos(angle)*distance,y:Math.sin(angle)*distance-15,opacity:0,duration:.5+(i%5)*.09,ease:'power2.out'},3.9);
    });
    // Force zero-time setters before any observer callback or screenshot.
    tl.time(.00001,true).pause(); faces();
    function final(){tl.pause().progress(1,true);faces();pause.hidden=true;}
    function play(){if(disposed)return;started=true;observer?.disconnect();if(reduced.matches){final();return;}pause.hidden=false;pause.textContent='Пауза';tl.restart();faces();}
    function motion(){if(reduced.matches)final();}
    replay.addEventListener('click',play);
    pause.addEventListener('click',()=>{if(tl.paused()){tl.resume();pause.textContent='Пауза';}else{tl.pause();pause.textContent='Продолжить';}});
    reduced.addEventListener('change',motion);
    const trigger=root.dataset.trigger||'inview';
    if(trigger==='click')replay.textContent='Запечатать письмо';
    // Wait for actual image decode before starting; a first visit must not
    // animate empty transparent layers while assets are still downloading.
    const backgrounds=[stage,get('back'),get('pocket'),inner,outer].map(el=>{
      const url=getComputedStyle(el).backgroundImage.match(/url\(["']?(.*?)["']?\)/)?.[1];
      if(!url)return Promise.resolve();
      const image=new Image();image.src=url;return image.decode();
    });
    const ready=Promise.allSettled([...root.querySelectorAll('img')].map(im=>im.decode()).concat(backgrounds));
    ready.then(()=>{
      if(disposed||started)return;
      if(reduced.matches){final();return;}
      if(trigger==='load'){play();return;}
      if(trigger==='click')return;
      observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting))play();},{threshold:.25});
      observer.observe(frame);
    });
    root.envelope={timeline:tl,play,fit,final,ready,destroy(){disposed=true;tl.kill();observer?.disconnect();resize.disconnect();mobile.removeEventListener('change',fit);reduced.removeEventListener('change',motion);particles.forEach(el=>el.remove());delete root.envelope;}};
    root.dispatchEvent(new CustomEvent('envelope:ready',{bubbles:true}));
  }
  function initAll(){document.querySelectorAll('.envelope').forEach(init);}
  window.EnvelopeSeal={init,initAll};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initAll,{once:true});else initAll();
})();
