window.onload = function () {
    let items = document.querySelectorAll('#default > tr');
    var colors = [];
    items.forEach(function (item) {
        let name = item.children[1].innerText;
        let code = item.children[2].innerText;
        let r = item.children[3].innerText;
        let g = item.children[4].innerText;
        let b = item.children[5].innerText;
        colors.push({'name': name.toLowerCase(), 'color': code, 'rgb': [r, g, b]});
    });
    document.getElementById('output').value = JSON.stringify(colors);
};
