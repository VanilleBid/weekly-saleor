export const getCookie = (name) => {
  let match = document.cookie.match(new RegExp(name + '=([^;]+)'));
  if (match) return match[1];
};

export const createCookie = (name, value, expire) => {
  document.cookie = name + '=' + value + '; expires=' + expire.toUTCString() + '; path=/';
};

export default $(document).ready(() => {
  const cookieName = 'cnil';
  let cookieContainer = document.getElementById('cookie_prompter');
  if (getCookie(cookieName) === '1' || !cookieContainer) {
    return;
  }
  let cookieBtn = cookieContainer.getElementsByTagName('button')[0];
  cookieBtn.addEventListener('click', function () {
    let d = new Date();
    d.setMonth(d.getMonth() + 3);
    createCookie('cnil', '1', d);
    cookieContainer.style.display = 'none';
  });
  cookieContainer.style.display = 'block';
});
