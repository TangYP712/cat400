let container = document.querySelector("#inner-wheel");
let btn = document.getElementById("spin");

let resetbtn = document.getElementById("reset");

let deg = 0;
let result = document.getElementById("outputR");


let zoneSize = 60; //deg

let chances = document.getElementById("ch").value;


const symbolZones = {
    1: "Thank You",
    2: "5% Off",
    3: "15% Off",
    4: "10% Off",
    5: "25% Off",
    6: "20% Off"
}

const handleWin = (actualDeg, chances) => {

    const winningNum = Math.ceil(actualDeg / zoneSize);
    var reward = symbolZones[winningNum];
    outputR.innerHTML = reward;

    chances = chances - 1;
    outputC.innerHTML = chances;
    document.getElementById("ch").value = chances;

    document.getElementById("resetchances").value = chances;
    document.getElementById("prize").value = reward;

    btn.style.pointerEvents = 'none';

    // if(chances > 0) {
    //     btn.onclick = () => {

    //         gameplay(chances);
            
    //     }
    // } else if(chances == 0 || chances < 0) {       
    //     btn.style.pointerEvents = 'none';      
    // }
}


function gameplay(chances) {
    deg = Math.floor(5000 + Math.random() * 5000);
    container.style.transition = 'all 1s ease-out';
	container.style.transform = "rotate(" + deg + "deg)";
    const actualDeg = (deg % 360);
    container.style.transform = "rotate(" + actualDeg + "deg)";
 
    setTimeout(() => {
        handleWin(actualDeg, chances);
    }, 1000);
}


btn.onclick = () => {

     if(chances == 0) {
        btn.style.pointerEvents = 'none';
        // btn.onclick = () => {
        //     btn.style.pointerEvents = 'none';
        // }
     }
     else {
        gameplay(chances);
     }

}