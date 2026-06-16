import { useState, useMemo } from "react"
import { COUNTRIES } from "../data/countries-cities"

interface LocationSelectorProps {
  country: string
  city: string
  onCountryChange: (country: string) => void
  onCityChange: (city: string) => void
  disabled?: boolean
}

export default function LocationSelector({
  country,
  city,
  onCountryChange,
  onCityChange,
  disabled = false,
}: LocationSelectorProps) {
  const [searchCountry, setSearchCountry] = useState("")
  const [searchCity, setSearchCity] = useState("")
  const [showCountryDropdown, setShowCountryDropdown] = useState(false)
  const [showCityDropdown, setShowCityDropdown] = useState(false)

  const selectedCountry = useMemo(
    () => COUNTRIES.find((c) => c.name === country) || null,
    [country],
  )

  const filteredCountries = useMemo(() => {
    const q = searchCountry.toLowerCase()
    if (!q) return COUNTRIES.slice(0, 30)
    return COUNTRIES.filter((c) =>
      c.name.toLowerCase().includes(q),
    ).slice(0, 30)
  }, [searchCountry])

  const filteredCities = useMemo(() => {
    if (!selectedCountry) return []
    const q = searchCity.toLowerCase()
    if (!q) return selectedCountry.cities.slice(0, 50)
    return selectedCountry.cities
      .filter((name) => name.toLowerCase().includes(q))
      .slice(0, 50)
  }, [selectedCountry, searchCity])

  return (
    <div className="space-y-4">
      {/* País */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          País <span className="text-red-500">*</span>
        </label>
        <div className="relative">
          <input
            type="text"
            placeholder="Buscar país..."
            value={searchCountry}
            onChange={(e) => {
              setSearchCountry(e.target.value)
              setShowCountryDropdown(true)
            }}
            onFocus={() => setShowCountryDropdown(true)}
            onBlur={() => setTimeout(() => setShowCountryDropdown(false), 200)}
            disabled={disabled}
            className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors disabled:opacity-50"
          />
          {showCountryDropdown && filteredCountries.length > 0 && (
            <ul className="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-lg max-h-48 overflow-y-auto">
              {filteredCountries.map((c) => (
                <li
                  key={c.iso}
                  onMouseDown={() => {
                    onCountryChange(c.name)
                    onCityChange("")
                    setSearchCountry(c.name)
                    setSearchCity("")
                    setShowCountryDropdown(false)
                  }}
                  className={`px-3.5 py-2 text-sm cursor-pointer hover:bg-emerald-50 transition-colors ${
                    c.name === country
                      ? "bg-emerald-50 text-emerald-700 font-medium"
                      : "text-slate-700"
                  }`}
                >
                  {c.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Ciudad */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Ciudad <span className="text-red-500">*</span>
        </label>
        {selectedCountry ? (
          <div className="relative">
            <input
              type="text"
              placeholder="Buscar ciudad..."
              value={searchCity}
              onChange={(e) => {
                setSearchCity(e.target.value)
                setShowCityDropdown(true)
              }}
              onFocus={() => setShowCityDropdown(true)}
              onBlur={() => setTimeout(() => setShowCityDropdown(false), 200)}
              disabled={disabled}
              className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors disabled:opacity-50"
            />
            {showCityDropdown && filteredCities.length > 0 && (
              <ul className="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-lg max-h-48 overflow-y-auto">
                {filteredCities.map((name) => (
                  <li
                    key={name}
                    onMouseDown={() => {
                      onCityChange(name)
                      setSearchCity(name)
                      setShowCityDropdown(false)
                    }}
                    className={`px-3.5 py-2 text-sm cursor-pointer hover:bg-emerald-50 transition-colors ${
                      name === city
                        ? "bg-emerald-50 text-emerald-700 font-medium"
                        : "text-slate-700"
                    }`}
                  >
                    {name}
                  </li>
                ))}
              </ul>
            )}
            {showCityDropdown && filteredCities.length === 0 && (
              <ul className="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-lg max-h-48 overflow-y-auto">
                <li className="px-3.5 py-2 text-sm text-slate-400">
                  No se encontraron ciudades
                </li>
              </ul>
            )}
          </div>
        ) : (
          <input
            type="text"
            placeholder={country ? "Escribe tu ciudad" : "Selecciona un país primero"}
            value={city}
            onChange={(e) => onCityChange(e.target.value)}
            disabled={disabled || !country}
            required
            className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors disabled:opacity-50"
          />
        )}
      </div>
    </div>
  )
}
