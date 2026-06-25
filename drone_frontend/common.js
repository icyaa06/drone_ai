const API = '/api';
const STATUS_LABELS = {submitted:'Заявка подана',screening:'Технический скрининг',stage2:'Stage 2 — прототип',regional_review:'Региональный отбор',finalist:'Финалист',declined:'Не прошла отбор'};
const MISSION_LABELS = {
  wildfire:'Wildfire Detection - forest fire detection on 100+ km²',
  agriculture:'Precision Agriculture - crop monitoring on 1000+ ha',
  rescue:'Search & Rescue - search over 50+ km²',
  medical:'Medical Delivery - essential cargo over 15+ km',
  infrastructure:'Infrastructure Monitoring - critical infrastructure inspection'
};

async function api(path, options={}) {
  const response = await fetch(`${API}${path}`, {credentials:'same-origin', ...options});
  const payload = await response.json().catch(()=>({success:false,message:'Некорректный ответ сервера'}));
  if (!response.ok) throw new Error(payload.message || 'Произошла ошибка');
  return payload;
}

document.querySelectorAll('.acc-button').forEach(button => button.addEventListener('click', () => button.parentElement.classList.toggle('open')));
document.querySelector('.menu-btn')?.addEventListener('click', () => {
  const links = document.querySelector('.nav-links');
  if (!links) return;
  links.style.display = links.style.display === 'flex' ? '' : 'flex';
  Object.assign(links.style,{position:'absolute',top:'76px',left:'0',right:'0',background:'#f4f3ed',padding:'22px',flexDirection:'column'});
});

document.querySelectorAll('[data-year]').forEach(el => el.textContent = new Date().getFullYear());
