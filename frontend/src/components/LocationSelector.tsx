import { useState, useMemo } from "react"
import { Country, State, City } from "country-state-city"
import type { ICountry } from "country-state-city"

const COUNTRY_NAMES_ES: Record<string, string> = {
  DO: "República Dominicana",
  MX: "México",
  CO: "Colombia",
  CR: "Costa Rica",
  US: "Estados Unidos",
  ES: "España",
  AR: "Argentina",
  CL: "Chile",
  PE: "Perú",
  EC: "Ecuador",
  GT: "Guatemala",
  CU: "Cuba",
  PR: "Puerto Rico",
  VE: "Venezuela",
  PA: "Panamá",
  HN: "Honduras",
  SV: "El Salvador",
  NI: "Nicaragua",
  BO: "Bolivia",
  PY: "Paraguay",
  UY: "Uruguay",
}

interface LocationSelectorProps {
  country: string
  city: string
  onCountryChange: (country: string) => void
  onCityChange: (city: string) => void
  disabled?: boolean
}

function getCountryLabel(c: ICountry): string {
  return COUNTRY_NAMES_ES[c.isoCode] || c.name
}

export default function LocationSelector({
  country,
  city,
  onCountryChange,
  onCityChange,
  disabled = false,
}: LocationSelectorProps) {
  const allCountries = useMemo(() => Country.getAllCountries(), [])
  const [searchCountry, setSearchCountry] = useState("")
  const [searchCity, setSearchCity] = useState("")
  const [showCountryDropdown, setShowCountryDropdown] = useState(false)
  const [showCityDropdown, setShowCityDropdown] = useState(false)

  const selectedCountryCode = useMemo(() => {
    const found = allCountries.find(
      (c) => c.name === country || COUNTRY_NAMES_ES[c.isoCode] === country
    )
    return found?.isoCode || ""
  }, [country, allCountries])

  const filteredCountries = useMemo(() => {
    const q = searchCountry.toLowerCase()
    if (!q) return allCountries.slice(0, 30)
    return allCountries
      .filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          (COUNTRY_NAMES_ES[c.isoCode] || "").toLowerCase().includes(q)
      )
      .slice(0, 30)
  }, [searchCountry, allCountries])

  const states = useMemo(() => {
    if (!selectedCountryCode) return []
    return State.getStatesOfCountry(selectedCountryCode) || []
  }, [selectedCountryCode])

  const hasStates = states.length > 0

  const filteredCities = useMemo(() => {
    if (!selectedCountryCode || !hasStates) return []
    // Use first state to get cities (some countries don't have states)
    const allCities: string[] = []
    for (const state of states) {
      const cities = City.getCitiesOfState(selectedCountryCode, state.isoCode) || []
      for (const c of cities) {
        allCities.push(c.name)
      }
    }
    const unique = [...new Set(allCities)]
    if (!searchCity) return unique.slice(0, 50)
    return unique
      .filter((name) => name.toLowerCase().includes(searchCity.toLowerCase()))
      .slice(0, 50)
  }, [selectedCountryCode, states, hasStates, searchCity])

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
              {filteredCountries.map((c) => {
                const label = getCountryLabel(c)
                return (
                  <li
                    key={c.isoCode}
                    onMouseDown={() => {
                      onCountryChange(label)
                      onCityChange("")
                      setSearchCountry(label)
                      setSearchCity("")
                      setShowCountryDropdown(false)
                    }}
                    className={`px-3.5 py-2 text-sm cursor-pointer hover:bg-emerald-50 transition-colors ${
                      label === country
                        ? "bg-emerald-50 text-emerald-700 font-medium"
                        : "text-slate-700"
                    }`}
                  >
                    {label}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>

      {/* Ciudad */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Ciudad <span className="text-red-500">*</span>
        </label>
        {hasStates ? (
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
              disabled={disabled || !country}
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
