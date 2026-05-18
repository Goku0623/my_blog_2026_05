import request from './index'

export interface AiWeatherParams {
  latitude?: number
  longitude?: number
  city?: string
}

export interface AiWeatherData {
  city: string
  temperature: number
  feels_like: number
  description: string
  humidity: number
  wind_speed: number
  icon: string
  updated_at: string
}

export interface WeatherCityLookupResult {
  name: string
  code: string
}

export const getWeather = (params: AiWeatherParams) => {
  return request.get<{ data: AiWeatherData }>('/ai/weather', { params })
}

export const lookupWeatherCityCode = (keyword: string) => {
  return request.get<{ data: WeatherCityLookupResult }>('/ai/admin/weather/city-lookup', {
    params: { keyword },
  })
}
