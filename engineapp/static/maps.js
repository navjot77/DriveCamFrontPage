/**
 * Created by navjotsingh on 2/23/17.
 */


// [VehicleLocation(key=Key('VehicleLocation', 4537134732017664), lat=37.376393,
// long=121.880617, name=u'vehicle102'),
// VehicleLocation(key=Key('VehicleLocation', 6736157987569664),
// lat=37.376393, long=121.880617, name=u'vehicle101')]

/*List of locations. Contains name of Restaurant, linkedId: Here is id which
is used later in ajax call to get restaurant related data from
FourSquare*/
/*var locations = [
    {
    'title': 'Vehicle 101',
    'location': {
        lat: 37.334273,
        lng: -121.889771
    }
}
];*/

//var name = $("script[src*='static/maps.js']").attr('src').split(',');
var locations = document.getElementById("helper").getAttribute("data-name");
//name1=name1.replace(/\[/g,'');
//name1=name1.replace(/\]/g,'');
//name1=name1.replace(/u/g,'');


locations=locations.split('&');
locations.pop()

for (var i=0; i<locations.length; i++){
   locations[i]=JSON.parse(locations[i]);
}
console.log(locations)

// global variables.
var map, infowindow;
// location of Map that will be point of center. This location is used in case
// User goes out of scope after zooms in/out.
var gCenter= {
        lat: 37.334273,
        lng: -121.889771
};
// Object for each location is stored.
//Here, show variable is made observable.
var model= function (data) {
    var self=this;
    self.name=data.title;
    // 'show' will be false in case when user searches for restaurant and that
    // restaurant name does not matches this object's restaurant name.
    self.show=ko.observable(true);
    // Setting the map marker at specific location.
    self.marker = new google.maps.Marker({
    position: data.location,
    map: map,
    title: data.title,
    animation: google.maps.Animation.DROP
    });
  // Setting the default color of marker as Blue.
  self.marker.setIcon('http://maps.google.com/mapfiles/ms/icons/blue-dot.png');

  // gotClicked function gets called when user clicks Item from List.
    // This function will animate the specific marker on maps.
  self.gotClicked=function(){
    // Resetting the zoom and center in case User navigates to other in maps.
 map.setCenter(gCenter);
  map.setZoom(10);
   if (self.marker.getAnimation() !== null) {
      self.marker.setAnimation(null);
  }
  else {
 self.marker.setIcon('http://maps.google.com/mapfiles/ms/icons/green-dot.png');
  self.marker.setAnimation(google.maps.Animation.BOUNCE);
  calling_api(self);

  window.setTimeout(function(){
  self.marker.setIcon('http://maps.google.com/mapfiles/ms/icons/blue-dot.png');
  self.marker.setAnimation(null);
       },2000);
  }
  };

  //Below function is called, when User clicks on the marker. This will
    // call the gotClicked function that call
    // foursqare api to set the content of infowindow.
  self.marker.addListener('click',self.gotClicked);

};

// Below function makes ajax call to foursqaure api and sets the infowindow.
var calling_api=function (self) {
        var infoContent=
            'Info..........';
        infowindow.setContent(infoContent);
        infowindow.open(map,self.marker);

};

// ViewModel, creates object for each restaurant and stores
// in observable array.
var ViewModel = function() {
    var self=this;
    self.list=ko.observableArray([]);
    self.query=ko.observable();

    for(i=0; i<locations.length;i++) {
        self.list.push(new model(locations[i]));
    }
    // This is called, when user does a keyUp event in search Bar.
    self.query.subscribe(function(value){
    if (value !== "") {
        var val = value.toLowerCase();
        var valRe = new RegExp(val + "\+");
        self.list().forEach(function (each, index) {
        if ((each.name.toLowerCase()).search(valRe) == -1) {
            each.show(false);
            each.marker.setMap(null);
             }
        else{
            each.marker.setMap(map);
            each.show(true);
            }
        });
    }
    else{
        self.list().forEach(function (each, index) {
        each.show(true);
        each.marker.setMap(map);
        });
        }
    });
};


function googleMap() {
map = new google.maps.Map(document.getElementById('map'), {
    center: {
        lat: 37.334273,
        lng: -121.889771
        },
    zoom: 12,
    mapTypeControl: false
    });


infowindow = new google.maps.InfoWindow();
infowindow.addListener('closeclick',function(){
         map.setCenter(gCenter);
        map.setZoom(11);
   });

ko.applyBindings(new ViewModel());
}
function error(){
    alert('Unable to Load Google Maps, check your internet Connection');
}

