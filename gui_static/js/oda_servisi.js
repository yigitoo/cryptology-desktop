const number = document.querySelector('#number');

function decrease() {
    if (parseInt(number.textContent) - 1 <= 0)
        number.textContent = 1;
    else
        number.textContent = parseInt(number.textContent)  - 1;
}

function increase() {
    if (parseInt(number.textContent) + 1 >= 10)
        number.textContent = 10;
    else
        number.textContent = parseInt(number.textContent) + 1;
}

async function send_form() {
    if(confirm("Siparişi göndermek istediğine emin misin?\nEminsen 'OK' değilsen 'Cancel'.") == true)
    {
        let response = await fetch(window.location.href, {
            method: "POST",
            body: JSON.stringify({
                "quantity": parseInt(number.textContent)
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        })

        let data = response.json();
    } 
}