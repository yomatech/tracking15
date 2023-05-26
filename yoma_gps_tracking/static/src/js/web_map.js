odoo.define('web_map.FieldMap', function(require) {
"use strict";

var field_registry = require('web.field_registry');
var AbstractField = require('web.AbstractField');
var FormController = require('web.FormController');

FormController.include({
    _update: function () {
        var _super_update = this._super.apply(this, arguments);
        this.trigger('view_updated');
        return _super_update;
    },
});

var FieldMap = AbstractField.extend({

    template: 'FieldMap',

    start: function() {
        var self = this;

        this.getParent().getParent().on('view_updated', self, function() {
            self.update_map();
            self.getParent().$('a[data-toggle="tab"]').on('shown.bs.tab', function() {
                self.update_map();
            });
        });
        return this._super();
    },

    _render: function () {
        this.init_map();
        this.isMap = true;
        this.update_mode();
        return this._super();
    },

    update_mode: function() {
        if(this.isMap) {
            if(this.mode === 'readonly') {
                this.map.setOptions({
                    disableDoubleClickZoom: true,
                    draggable: true,// me fix
                    scrollwheel: true,// me fix
                });
                this.markerCluster.setOptions({
                    draggable: false,
                    cursor: 'default',
                });
            } else {
                this.map.setOptions({
                    disableDoubleClickZoom: false,
                    draggable: true,
                    scrollwheel: true,
                });
                this.markerCluster.setOptions({
                    draggable: true,
                    cursor: 'pointer',
                });
            }
        }
    },

    update_map: function() {
        if(!this.isMap && this.el.offsetWidth > 0) {

            this.init_map();
            this.isMap = true;
        }
        this.update_mode();
    },

    init_map: function() {
        var self = this;

        this.isEmpty = function(obj) {
                    for(var key in obj) {
                        if(obj.hasOwnProperty(key))
                            return false;
                    }
                    return true;
                }

        this.zoomToObject = function (obj){
            var bounds = new google.maps.LatLngBounds();
            var points = obj.getPath().getArray();
            for (var n = 0; n < points.length ; n++){
                bounds.extend(points[n]);
            }
            this.map.fitBounds(bounds);
        }

        this.iconUrl = '/web_google_maps/static/src/img/markers/';

        this.position = new google.maps.LatLng(0, 0);

        this.map = new google.maps.Map(this.el, {
            center: this.position,
            disableDefaultUI: true,
        });

        this.polyinfo = new google.maps.InfoWindow();

        this.markerinfo = new google.maps.InfoWindow();

        this.waypoints = new google.maps.Polyline({
                            path: [],
                            geodesic: true,
                            strokeColor: '#0000FF',
                            strokeOpacity: 1.0,
                            strokeWeight: 2
                            });

        this.markerCluster = new MarkerClusterer(this.map, this.markers,{
            maxZoom: 17,
            zoomOnClick: false
        });

        this.info_windows = [];

        this.zoom = 17;

        this.markers = [];

        this.point_array = [];

        this.route = [];
        this.start_route = false;
        this.end_route = false;

        this.bounds = new google.maps.LatLngBounds();

        if(this.value) {

            var data = JSON.parse(this.value);

            this.zoom = data.zoom

            if(data.makers){

                for (var index in data.makers) {

                    var parsedMarker = JSON.parse(data.makers[index]);
                    var position = new google.maps.LatLng(parsedMarker.lat, parsedMarker.lng);

                    this.route.push({
                        location:position,
                        stopover: true
                        });
                    this.map.setCenter(position);

                    var marker = new google.maps.Marker({
                        position: position,
                        map: this.map,
                        title: parsedMarker.info || '',
                        icon: {
                            url: this.iconUrl + parsedMarker.color.trim() + '.png'
                        },

                    });

                    google.maps.event.addListener(marker, 'click', function(event) {
                        if(event){
                            const info_window = new google.maps.InfoWindow({
                            content:self.info_windows[this.index]
                          });
                            info_window.setPosition(event.latLng);
                            info_window.open(self.map);
                        }
                    })

                    this.info_windows.push(
                    '<div  id="content" class="o_kanban_view o_res_partner_kanban o_kanban_ungrouped">'+
                        '<div class="oe_kanban_details d-flex flex-column">'+
                            '<strong id="firstHeading" class="o_kanban_record_title">'+
                                '<span>'+parsedMarker.info+'</span>'+
                            '</strong>' +
                            '<ul id="bodyContent" class="list-group list-group-flush">'+
                                '<li class="list-group-flush-item">'+parsedMarker.city+', '+parsedMarker.country_id+'</li>'+
                                '<li class="list-group-flush-item">'+parsedMarker.email+'</li>'+
                            '</ul>'+
                        '</div>'+
                    '</div>');
                    marker.index = index;
                    this.markers.push(marker);
                    this.markerCluster.addMarker(marker);
                    this.bounds.extend(position);

                }

                this.map.fitBounds(this.bounds);

                if(this.route.length >= 2){

                    this.end_route = this.route.pop();
                    this.start_route = this.route.shift();

                    var directionsService = new google.maps.DirectionsService;
                    var directionsDisplay =  new google.maps.DirectionsRenderer({suppressMarkers: true});

                    directionsDisplay.setMap(this.map);

                    directionsService.route({
                        origin: this.start_route.location,
                        destination: this.end_route.location,
                        waypoints: this.route,
                        optimizeWaypoints: true,
                        travelMode: google.maps.DirectionsTravelMode.DRIVING,
                        unitSystem: google.maps.UnitSystem.METRIC
                    }, function(response, status) {
                            if (status === 'OK') {
                                directionsDisplay.setDirections(response);
                            }
                        }
                    );
                }
            }

            if(data.waypoints){

                var array_of_wp = []
                var info = []
                data.waypoints.forEach(function(value) {
                var parsedPoint = JSON.parse(value);
                var position = new google.maps.LatLng(parsedPoint.lat,parsedPoint.lng);
                    array_of_wp.push(position);

                });

                this.info = info;

                this.waypoints.setPath(array_of_wp);

                this.waypoints.setMap(this.map);

                this.point_array = array_of_wp;

                this.zoomToObject(this.waypoints);

             }

            if (this.isEmpty(data.makers) && this.isEmpty(data.waypoints)){

                var default_value = JSON.parse(data.default_value);

                if(default_value){

                    this.position = new google.maps.LatLng(default_value.lat, default_value.lng);
                    this.map.setCenter(this.position);

                    var marker = new google.maps.Marker({
                        map: this.map,
                        visible: false,
                        position: this.position
                    });

                    this.markerCluster.addMarker(marker);

                    this.bounds.extend(this.position);

                    this.map.fitBounds(this.bounds);

                }
            }

        }

        this.map.addListener('click', function(e) {
            if(self.mode === 'edit' && self.marker.getMap() == null) {
                self.marker.setPosition(e.latLng);
                self.marker.setMap(self.map);
                self._setValue(JSON.stringify({position:self.marker.getPosition(),zoom:self.map.getZoom()}));
            }
        });

        this.map.addListener('zoom_changed', function() {
            if(self.mode === 'edit' && self.marker.getMap()) {
                self._setValue(JSON.stringify({position:self.marker.getPosition(),zoom:self.map.getZoom()}));
            }
        });

        this.map.addListener('idle', function(event){

           if (this.getZoom() >= 21){
               this.setZoom(self.zoom);
           }

        });

        this.markerCluster.addListener('click', function() {
            if(self.mode === 'edit') {
                self.marker.setMap(null);
                self._setValue(false);
            }
        });

        this.markerCluster.addListener('dragend', function()
        {
            self._setValue(JSON.stringify({position:self.marker.getPosition(),zoom:self.map.getZoom()}));
        });
        this.waypoints.addListener('mouseover', function (event) {
            if(event)
            {
                var minDist = Number.MAX_VALUE;
                var index;
                for (var i=0; i<this.getPath().getLength(); i++){
                    var distance = google.maps.geometry.spherical.computeDistanceBetween(event.latLng, this.getPath().getAt(i));
                    if (distance < minDist) {
                      minDist = distance;
                      index = i;
                    }
                  }

                self.polyinfo.setPosition(event.latLng);
                self.polyinfo.setContent(self.info[index]);
                self.polyinfo.open(self.map);

            }

        });
        this.waypoints.addListener('mouseout', function (event) {
            self.polyinfo.close();

        });
    },

});

field_registry.add('google_map', FieldMap);

return {

    FieldMap: FieldMap,

};

});