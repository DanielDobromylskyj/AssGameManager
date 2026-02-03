// Adds a header to the page

const head = `<link rel="stylesheet" href="/public/css/header.css">`
const body = `
<header>
    <h1>UEA Assassins Society - Game Hosting</h1>
</header>

`;


document.head.innerHTML += head;
document.body.innerHTML = body + document.body.innerHTML;


