// Global latitude and longiitude
const globalLat = 43;
const globalLong = 11;

//Data is usable here
var max_year = -Number.MAX_VALUE;
var min_year = Number.MAX_VALUE;

// Index containing the year, and maps the value selected on the slider 
var dictYearsObj = {};
var global_results = null;
var composer_links = null;
var latLongMap = {};
var markersCurrently = [];
var zoomClick = false;
var lastCityClicked = null;
var yearSelected = null;

// Indexes for array to trace in the data we retrieve from CSV
const TITLE_INDEX = 4;
const YEAR_INDEX = 5;
const CITY_INDEX = 9;
const LAT_INDEX = 10;
const LONG_INDEX = 11;
const COMPOSER_INDEX = 16;
const THEATER_NAME = 20;
const THEATER_LAT = 21;
const THEATER_LONG = 22;

var mymap = L.map('mapid').setView([globalLat, globalLong], 6);

// Stop the map from moving on left and right, by user input
mymap.dragging.disable();

// Public token (for mapbox): pk.eyJ1IjoiaGFyc2hjczE5OTYiLCJhIjoiY2tndGdrcmZ3MGF0ZjJ6cGVtenNlMXdzOCJ9.xXRLIH9aN6I7W9bHyXK-ag

var tileLayer = L.tileLayer('http://{s}.tile.stamen.com/toner-background/{z}/{x}/{y}.png', {
    attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
    subdomains: 'abcd',
    // Fix the zoom, so that users cannot move the zoom
    minZoom: 5,
    maxZoom: 15
}).addTo(mymap);
tileLayer.setOpacity(0.7);

// Adding leaf icon for marker
var LeafIcon = L.Icon.extend({
    options: {
      iconSize:     [28, 75],
      // iconAnchor:   [22, 94],
      // popupAnchor:  [-3, -76]
    }
});

// Adding icon for libretto
var librettoIcon = new LeafIcon({iconUrl: 'book-solid.svg'});
// Adding icon for theatre
var theatreIcon = new LeafIcon({iconUrl: 'landmark-solid.svg'});


function doStuff(data) {
    //Data is usable here
    var years = [];

    data.forEach(function (o) {
      if (typeof o[YEAR_INDEX] !== 'string') {
        years.push(parseInt(o[YEAR_INDEX], 10));
      }
    });

   years = years.slice(0, 692);
   min_year = Math.min(...years);
   max_year = Math.max(...years);

   // Taking the range for every 22 years
   var ranges = _.range(min_year, max_year, 22);
   var total_ranges = ranges.length;

   // Setting the range of the slider and setting the half value
   document.getElementById('myRange').max = (total_ranges - 1) * 10;
   document.getElementById('myRange').value = (parseInt(total_ranges / 2, 10) + 3) * 10;

   // get the wrapper element for adding the ticks
   var step_list = document.getElementsByClassName('menuwrapper')[0];
   var step_list_two = document.getElementsByClassName('menuwrapper2')[0];

   // Adding years with marking on the slider as p tags
   for (var index = 0; index <= total_ranges - 1; index++) {
     dictYearsObj[index] = ranges[index];
     var span = document.createElement("span");
     span.style.marginTop = "-14px";
     span.style.marginLeft = "2px";
     span.innerHTML = '|';
     step_list.appendChild(span);

     // for the labels
     var span_two = document.createElement("span");
     span_two.innerHTML = ranges[index];
     span_two.style.marginTop = "-14px";
     step_list_two.appendChild(span_two);
   }
}

// Parse data from papa parse CSV
function parseData(url, callBack) {
  Papa.parse(url, {
    download: true,
    dynamicTyping: true,
    complete: function(results) {
        // Assigning the results so that we can play with it
        global_results = results.data;
        callBack(results.data);
    }
  });
}

parseData("http://0.0.0.0:1234/data/get_librettos_dummies.csv", doStuff);
// Create a promise to load the file or throw an error
dfd.read_csv("http://0.0.0.0:1234/data/composer_links.csv")
.then(df => {
    composer_links = df;
    console.log("Loaded the composer links");
}).catch(err => {
    console.log(err);
})


function insertDropdown () {
  // Make dropdown menu
  var div = document.createElement('select');
  div.setAttribute("name", "platform");
  // This will not work for more than 2 sequences
  var option = document.createElement('option');
  option.setAttribute("value", 0);
  option.innerHTML = 'Original Map sequence';
  div.appendChild(option);
  var option_two = document.createElement('option');
  option_two.setAttribute("value", 1);
  option_two.innerHTML = 'Cities composer played';
  div.appendChild(option_two);
  return div
}

function createLinks() {
  var sameYearComposer = composer_links.query(
    {column: "lower_bounds", is: "==", to: "1760"});
  var allCitiesLabels = [];
  for(let i=0; i < sameYearComposer.shape[0]; i++) {
    var city_list = sameYearComposer['cities'].data[i].replace(
      '}', '').replace('{', '').replace(/'/g,'').split(', ');
    allCitiesLabels.push('cityMarker-' + city_list[0]);
    allCitiesLabels.push('cityMarker-' + city_list[1]);
    // From src to the destination
    var pointList = [latLongMap[city_list[0]], latLongMap[city_list[1]]];
    var link_path = new L.Polyline(pointList, {
      color: 'red',
      weight: 3,
      opacity: 0.5,
      smoothFactor: 1,
      className: 'linkLine'
    });
    console.log(link_path);
    link_path.addTo(mymap);
  }
  document.querySelectorAll("[id^='cityMarker-']").forEach(function(o) {
    if(allCitiesLabels.includes(o.id)) {
      o.style.display = 'initial';
    } else {
      o.style.display = 'none';
    }
  })
}

function deleteLinks() {
  document.querySelectorAll("[id^='cityMarker-']").forEach(function(o) {
    o.style.display = 'initial';
  });
  var allLinkLines = document.getElementsByClassName("linkLine");
  // pop off each of the theatre markers
  while (allLinkLines.length > 0) {
    allLinkLines[0].parentNode.removeChild(allLinkLines[0]);
  }
}

function hoverAndDoThings(mouseObj) {
    // Make a textual pane when we find the city and click on the point
    // and then we remove it, when we click on something else
    var scrollTextPane = document.getElementById('scrollText');
    var city_name = mouseObj._tooltip._content.split(":")[2].replace(/\s+/, "");

    // Remove the panel cards if some of them exists already
    if(scrollTextPane.children.length !== 0) {
      var panels = document.getElementsByClassName("w3-panel w3-blue w3-card-4");
      // pop off each of the panels
      while (panels.length > 0) {
        panels[0].parentNode.removeChild(panels[0]);
      }
      var heading = document.getElementsByClassName("headingFDHPanel")[0];
      heading.parentNode.removeChild(heading);
    }

    // Adding heading for the right bar
    var h4 = document.createElement("h4");
    h4.setAttribute("class", "headingFDHPanel");
    h4.innerHTML = "List of Librettos for years: " + "<b>" + yearSelected + "-" + (yearSelected + 22) + "</b>" + " in city: " + "<b>" + city_name + "</b>";
    h4.style.fontSize = "21px";
    h4.style.textAlign = "center";
    scrollTextPane.appendChild(h4);

    global_results.forEach(function (o) {
      if ((typeof o[YEAR_INDEX] !== 'string') && ((o[YEAR_INDEX] >= yearSelected && (o[YEAR_INDEX] < yearSelected + 22))) && (o[CITY_INDEX] === city_name)) {
        var div = document.createElement("div");
        div.setAttribute("class", "w3-panel w3-blue w3-card-4");

        // Adding title pane
        var p_title = document.createElement("p");
        p_title.innerHTML = "Title";
        p_title.style.fontSize = "15px";

        var p_title_text = document.createElement("p");
        p_title_text.innerHTML = o[TITLE_INDEX];
        p_title_text.style.fontSize = "10px";

        // Adding year pane
        var p_title_year = document.createElement("p");
        p_title_year.innerHTML = "Year";
        p_title_year.style.fontSize = "15px";

        var p_title_year_text = document.createElement("p");
        p_title_year_text.innerHTML = o[YEAR_INDEX];
        p_title_year_text.style.fontSize = "10px";

        // Add composer information to the information pane
        var p_title_composer = null;
        var p_title_composer_text = null;
        var dropdown_div = null;
        var composer_div = null;
        if(o[COMPOSER_INDEX] !== 'Not found') {
          p_title_composer = document.createElement("p");
          p_title_composer.innerHTML = "Composer";
          p_title_composer.style.fontSize = "15px";
          p_title_composer.style.display = "inline";
        }

        // Adding the paras to each child
        div.appendChild(p_title);
        div.appendChild(p_title_text);
        div.appendChild(p_title_year);
        div.appendChild(p_title_year_text);
        if(p_title_composer != null) {
          p_title_composer_text = document.createElement("p");
          p_title_composer_text.innerHTML = o[COMPOSER_INDEX];
          p_title_composer_text.style.fontSize = "10px";
          // Create only dropdowns where we can see the multiple links
          if(composer_links['lower_bounds'].data.includes(yearSelected) && composer_links["composer"].data.includes(o[COMPOSER_INDEX])) {
            composer_div = document.createElement("div");
            composer_div.appendChild(p_title_composer);
            dropdown_div = insertDropdown();
            dropdown_div.style.display = "inline";
            dropdown_div.style.marginLeft = "5px";

            dropdown_div.onchange = function () {
              if(dropdown_div.selectedIndex == 0) {
                tileLayer.setOpacity(0.7);
                deleteLinks();
              } else {
                tileLayer.setOpacity(0.4);
                createLinks();
              }
            };
            composer_div.appendChild(dropdown_div);
            composer_div.style.width = "100%";
            div.appendChild(composer_div);
          } else {
            div.appendChild(p_title_composer);
          }
          div.appendChild(p_title_composer_text);
        }
        scrollTextPane.appendChild(div);
      }
    });
}

function plotIntensityMap(cityCount, subTheatres, totalLibrettoCount) {
    var allCityMarkers = []
    Object.keys(cityCount).forEach(function(o){
        var lat = latLongMap[o][0];
        var long = latLongMap[o][1];
        // Adding a marker and an associated popup
        // Use circle marker to get the right radius
        var int_rad = cityCount[o] === 1 ? (0.01/ totalLibrettoCount) : (cityCount[o] / totalLibrettoCount);
        // [0,1] => [2,25]
        var map_int_rad = 10 + ((int_rad * 23)/(0.5))
        var marker = L.marker(
          [lat, long], {icon: librettoIcon}).addTo(mymap);
            // color: 'grey', fillColor: 'rgb(123,61,63)', 
            // fillOpacity: 0.9, radius: map_int_rad})
        marker._icon.id = "cityMarker-" + o;
        marker.bindTooltip("Number of librettos: " + cityCount[o] + " in city of: " + o, {
            permanent: false, className: "my-label", offset: [0, 0]
        });

        // Get all the city markers
        allCityMarkers.push(marker.getElement());

        marker.on('click', function(){
          var temp_city_name = this._tooltip._content.split(":")[2].replace(/\s+/, "");
          if(!zoomClick && ((temp_city_name !== lastCityClicked) || (lastCityClicked === null))) {
            hoverAndDoThings(this);
            lastCityClicked = temp_city_name;
          } else {
            // Zoom in into the point if you click again
            console.log("Inside else 2 clicks", subTheatres);
              for (var key in subTheatres) {
                var key_list = key.split(',');
                var key_city_name = key_list[0];
                var key_lat = key_list[1];
                var key_long = key_list[2];
                if(temp_city_name === key_city_name) {
                  var theatre_marker = L.marker(
                    [key_lat, key_long], 
                    {icon: theatreIcon}
                    // {color: 'skyblue', fillColor: 'black', fillOpacity: 0.2, radius: 10}
                    ).addTo(mymap);
                  theatre_marker._icon.classList.add("theatreMarker"); // path.leaflet-interactive.theatreMarker

                  // Adding comment for the subtheaters
                  var city_string = '';
                  city_string += "<br>";
                  for (const [index, element] of subTheatres[key].entries()) { 
                    city_string += (index + 1) + ". " + element;
                    city_string += "<br>";
                  }
                  console.log(city_string);
                  theatre_marker.bindTooltip("For theaters: " + city_string + " in city of: " + temp_city_name, {
                    permanent: false, className: "my-theater-label", offset: [0, 0]
                  });
                  theatre_marker.on('click', function(){
                    revertBackToCityView(allCityMarkers);
                    lastCityClicked = null;
                  });
                }
              }

              // Remove all the city markers since we are zoomed into a region
              for(i = 0; i < allCityMarkers.length; i++) {
                allCityMarkers[i].style.display = 'none';
              }
              mymap.flyTo([latLongMap[temp_city_name][0], latLongMap[temp_city_name][1]], 14);
              lastCityClicked = temp_city_name;
              zoomClick = false;
            }
        });
        mymap.addLayer(marker);
        markersCurrently.push(marker);
    });
}

function revertBackToCityView(allCityMarkers) {
  // Check if you are zoomed in or not, if you are zoom out
  var allTheatreMarkers = document.getElementsByClassName("theatreMarker");
  var allTheatreLabels = document.getElementsByClassName("my-theater-label");
  // pop off each of the theatre markers
  while (allTheatreMarkers.length > 0) {
    allTheatreMarkers[0].parentNode.removeChild(allTheatreMarkers[0]);
  }

  while (allTheatreLabels.length > 0) {
    allTheatreLabels[0].parentNode.removeChild(allTheatreLabels[0]);
  }

  // Set the display back for all the city markers
  for(i = 0; i < allCityMarkers.length; i++) {
    allCityMarkers[i].style.display = 'initial';
  }
  mymap.flyTo([globalLat, globalLong], 6);
  zoomClick = false;
}

// Detecting the slider in HTML
var slider = document.getElementById("myRange");

// Update the current slider value (each time you drag the slider handle)
slider.oninput = function() {
  // Remove any exists markers which might be present on the map
  if(markersCurrently.length !== 0) {
    for (var index = 0; index < markersCurrently.length; index++) {
        mymap.removeLayer(markersCurrently[index]);
    }
    markersCurrently = [];
  }

  var value_selected = slider.value / 10;
  yearSelected = dictYearsObj[value_selected];

  var getIntensityCount = {};
  var getSubTheatres = {};
  var totalLibrettoCount = 0;
  global_results.forEach(function (o) {
    if ((typeof o[YEAR_INDEX] !== 'string') && ((o[YEAR_INDEX] >= yearSelected) && (o[YEAR_INDEX] < yearSelected + 22))) {
        latLongMap[o[CITY_INDEX]] = [o[LAT_INDEX], o[LONG_INDEX]];
        getIntensityCount[o[CITY_INDEX]] = (getIntensityCount[o[CITY_INDEX]] || 0) + 1;

        var basic_key = o[CITY_INDEX] + ',' + o[THEATER_LAT] + ',' + o[THEATER_LONG];
        if((o[THEATER_LAT] !== 'Not found') && (o[THEATER_LONG] !== 'Not found')) {
            getSubTheatres[basic_key] = getSubTheatres[basic_key] || [];
        }

        // Do not put in the sub theaters which have lat long and not found
        if((o[THEATER_LAT] !== 'Not found') && (o[THEATER_LONG] !== 'Not found')) {
          if (basic_key in getSubTheatres) {
            getSubTheatres[basic_key].push(o[THEATER_NAME]);
          }
        }
        totalLibrettoCount += 1
    }
  });

  console.log('harsh', getSubTheatres);
  plotIntensityMap(
    getIntensityCount, getSubTheatres, totalLibrettoCount);
}
