import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Users, UserPlus, ClipboardText, BowlFood } from "@phosphor-icons/react";
import { getDashboard } from "../services/api";
import type { DashboardSummary } from "../types";
import { KpiCard } from "../components/dashboard/KpiCard";
import { ActivityTimeline } from "../components/dashboard/ActivityTimeline";
import { ProfileProgress } from "../components/dashboard/ProfileProgress";
import { SkeletonCard, Skeleton, SkeletonRow } from "../components/ui/Skeleton";

const containerVariants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const },
  },
};

export default function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    setLoading(true);
    setError(null);
    getDashboard()
      .then((d) => setData(d))
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getDashboard()
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Error");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={fetchData}
          className="bg-emerald-600 text-white px-6 py-2 rounded-full hover:bg-emerald-700 transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <h1 className="text-xl font-semibold text-slate-800 mb-6">Dashboard</h1>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-2xl p-6 space-y-3">
            <Skeleton className="h-5 w-40" />
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <SkeletonRow key={i} />
              ))}
            </div>
          </div>
          <div className="lg:col-span-1 bg-white rounded-2xl p-6 space-y-4">
            <Skeleton className="h-5 w-44" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-2 w-full" />
            <div className="flex gap-4">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-24" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* istanbul ignore next — safety guard; data is guaranteed after loading */
  if (!data) return null;

  const complete = data.total_patients - data.incomplete_profiles;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-xl font-semibold text-slate-800 mb-6 md:hidden">
        Dashboard
      </h1>

      <motion.div
        className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        <motion.div variants={itemVariants}>
          <KpiCard
            label="Total pacientes"
            value={data.total_patients}
            icon={<Users size={24} weight="duotone" />}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <KpiCard
            label="Nuevos este mes"
            value={data.new_patients_30d}
            icon={<UserPlus size={24} weight="duotone" />}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <KpiCard
            label="Perfiles incompletos"
            value={data.incomplete_profiles}
            icon={<ClipboardText size={24} weight="duotone" />}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <KpiCard
            label="Dietas generadas"
            value={data.diets_generated}
            icon={<BowlFood size={24} weight="duotone" />}
          />
        </motion.div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          className="lg:col-span-2 bg-white rounded-2xl p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.4,
            duration: 0.5,
            ease: [0.16, 1, 0.3, 1] as const,
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800">
              Actividad reciente
            </h2>
            <a
              href="/patients"
              className="text-sm font-medium text-emerald-600 hover:text-emerald-700 transition-colors"
            >
              Ver todos &rarr;
            </a>
          </div>
          <ActivityTimeline activities={data.latest_activity} />
        </motion.div>

        <motion.div
          className="lg:col-span-1 bg-white rounded-2xl p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.5,
            duration: 0.5,
            ease: [0.16, 1, 0.3, 1] as const,
          }}
        >
          <h2 className="text-lg font-semibold text-slate-800 mb-4">
            Perfiles completados
          </h2>
          <ProfileProgress
            total={data.total_patients}
            complete={complete}
            incomplete={data.incomplete_profiles}
          />
        </motion.div>
      </div>
    </div>
  );
}
