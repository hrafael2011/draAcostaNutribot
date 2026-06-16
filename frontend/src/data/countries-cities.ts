export interface CountryData {
  iso: string
  name: string
  cities: string[]
}

export const COUNTRIES: CountryData[] = [
  {
    iso: "DO",
    name: "República Dominicana",
    cities: [
      "Santo Domingo", "Santiago", "La Romana", "San Pedro de Macorís",
      "Punta Cana", "Puerto Plata", "La Vega", "San Francisco de Macorís",
      "San Cristóbal", "Higüey", "Moca", "Bonao", "Baní", "Barahona",
      "Azua", "Hato Mayor", "Salcedo", "Nagua", "Samaná", "Jarabacoa",
      "Sosúa", "Las Terrenas", "Cotuí", "Monte Cristi", "Mao",
      "Villa Altagracia", "Constanza", "Bayaguana", "Sabana de la Mar",
    ],
  },
  {
    iso: "MX",
    name: "México",
    cities: [
      "Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Mérida",
      "Cancún", "Tijuana", "León", "Querétaro", "San Luis Potosí",
      "Toluca", "Hermosillo", "Culiacán", "Chihuahua", "Morelia",
      "Aguascalientes", "Mexicali", "Acapulco", "Puerto Vallarta",
      "Oaxaca", "Guanajuato", "Villahermosa", "Durango", "Veracruz",
    ],
  },
  {
    iso: "CO",
    name: "Colombia",
    cities: [
      "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
      "Bucaramanga", "Pereira", "Cúcuta", "Santa Marta", "Ibagué",
      "Manizales", "Pasto", "Villavicencio", "Armenia", "Neiva",
      "Popayán", "Montería", "Sincelejo", "Valledupar", "Tunja",
      "San Andrés", "Leticia",
    ],
  },
  {
    iso: "CR",
    name: "Costa Rica",
    cities: [
      "San José", "Alajuela", "Heredia", "Cartago", "Liberia",
      "Puntarenas", "Limón", "Guanacaste", "Ciudad Quesada",
      "San Isidro del General",
    ],
  },
  {
    iso: "US",
    name: "Estados Unidos",
    cities: [
      "New York", "Los Angeles", "Chicago", "Houston", "Miami",
      "Orlando", "Atlanta", "Dallas", "San Antonio", "Austin",
      "Boston", "Phoenix", "Denver", "Seattle", "San Francisco",
      "Las Vegas", "Washington D.C.", "Philadelphia", "Tampa",
      "San Juan",
    ],
  },
  {
    iso: "ES",
    name: "España",
    cities: [
      "Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga",
      "Bilbao", "Zaragoza", "Alicante", "Granada", "Palma de Mallorca",
      "Murcia", "Tenerife", "Córdoba", "Valladolid", "Salamanca",
      "Toledo", "Santiago de Compostela",
    ],
  },
  {
    iso: "AR",
    name: "Argentina",
    cities: [
      "Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata",
      "Mar del Plata", "San Miguel de Tucumán", "Salta", "Santa Fe",
      "Bariloche", "Ushuaia", "Neuquén", "Posadas", "San Juan",
    ],
  },
  {
    iso: "CL",
    name: "Chile",
    cities: [
      "Santiago", "Valparaíso", "Concepción", "La Serena", "Antofagasta",
      "Viña del Mar", "Temuco", "Rancagua", "Arica", "Iquique",
      "Punta Arenas", "Puerto Montt",
    ],
  },
  {
    iso: "PE",
    name: "Perú",
    cities: [
      "Lima", "Arequipa", "Cusco", "Trujillo", "Chiclayo",
      "Piura", "Iquitos", "Huancayo", "Tacna", "Puno",
    ],
  },
  {
    iso: "EC",
    name: "Ecuador",
    cities: [
      "Quito", "Guayaquil", "Cuenca", "Santo Domingo", "Machala",
      "Manta", "Loja", "Ambato", "Esmeraldas", "Quevedo",
    ],
  },
  {
    iso: "GT",
    name: "Guatemala",
    cities: [
      "Ciudad de Guatemala", "Mixco", "Villa Nueva", "Quetzaltenango",
      "Escuintla", "Antigua Guatemala", "Chimaltenango", "Huehuetenango",
      "Cobán", "Mazatenango",
    ],
  },
  {
    iso: "CU",
    name: "Cuba",
    cities: [
      "La Habana", "Santiago de Cuba", "Camagüey", "Holguín",
      "Santa Clara", "Cienfuegos", "Matanzas", "Pinar del Río",
      "Bayamo", "Las Tunas",
    ],
  },
  {
    iso: "PR",
    name: "Puerto Rico",
    cities: [
      "San Juan", "Bayamón", "Carolina", "Ponce", "Caguas",
      "Mayagüez", "Arecibo", "Guaynabo", "Trujillo Alto", "Fajardo",
    ],
  },
  {
    iso: "VE",
    name: "Venezuela",
    cities: [
      "Caracas", "Maracaibo", "Valencia", "Barquisimeto", "Maracay",
      "Ciudad Guayana", "Mérida", "San Cristóbal", "Barcelona",
      "Puerto La Cruz", "Cumaná", "Porlamar",
    ],
  },
  {
    iso: "PA",
    name: "Panamá",
    cities: [
      "Ciudad de Panamá", "San Miguelito", "David", "Colón",
      "La Chorrera", "Santiago", "Penonomé", "Chitré", "Las Tablas",
      "Bocas del Toro",
    ],
  },
  {
    iso: "HN",
    name: "Honduras",
    cities: [
      "Tegucigalpa", "San Pedro Sula", "La Ceiba", "Choloma",
      "El Progreso", "Comayagua", "Puerto Cortés", "Danlí",
      "Siguatepeque", "Juticalpa",
    ],
  },
  {
    iso: "SV",
    name: "El Salvador",
    cities: [
      "San Salvador", "Santa Ana", "San Miguel", "Soyapango",
      "Apopa", "Mejicanos", "Sonsonate", "Usulután", "Cojutepeque",
    ],
  },
  {
    iso: "NI",
    name: "Nicaragua",
    cities: [
      "Managua", "León", "Granada", "Masaya", "Estelí",
      "Chinandega", "Matagalpa", "Jinotega", "Rivas", "Bluefields",
    ],
  },
  {
    iso: "BO",
    name: "Bolivia",
    cities: [
      "Santa Cruz de la Sierra", "La Paz", "Cochabamba", "Sucre",
      "Oruro", "Tarija", "Potosí", "El Alto", "Trinidad", "Cobija",
    ],
  },
  {
    iso: "PY",
    name: "Paraguay",
    cities: [
      "Asunción", "Ciudad del Este", "Encarnación", "Luque",
      "San Lorenzo", "Capiatá", "Lambaré", "Fernando de la Mora",
      "Caaguazú", "Salto del Guairá",
    ],
  },
  {
    iso: "UY",
    name: "Uruguay",
    cities: [
      "Montevideo", "Salto", "Paysandú", "Maldonado", "Punta del Este",
      "Rivera", "Tacuarembó", "Colonia del Sacramento", "Mercedes",
      "Artigas",
    ],
  },
]
