#!/bin/sh
# Configure using https://www.theweather.com/widget/
curl "https://www.theweather.com/wimages/foto3c0142c5f2f6287ab38d28f989a419d4.png" > weather.png
convert -crop 178x85+0+30 weather.png weather_crop.png
lp -o orientation-requested=3 weather_crop.png
rm weather.png weather_crop.png

