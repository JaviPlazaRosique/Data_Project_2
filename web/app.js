function initMap() {
    const ubicacionInicial = { lat: 40.416775, lng: -3.703790 }; // Madrid

    const map = new google.maps.Map(document.getElementById("map"), {
        zoom: 12,
        center: ubicacionInicial,
    });

    new google.maps.Marker({
        position: ubicacionInicial,
        map: map,
        title: "Ubicación Inicial"
    });
}

window.initMap = initMap;

async function loadGoogleMaps() {
    try {
        const response = await fetch('./config.json');
        const config = await response.json();
        const apiKey = config.GOOGLE_MAPS_API_KEY;

        if (!apiKey) {
            console.error("No se encontró la API Key en config.json");
            return;
        }

        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=initMap&v=weekly`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);

    } catch (error) {
        console.error("Error cargando el mapa o la configuración:", error);
    }
}

loadGoogleMaps();