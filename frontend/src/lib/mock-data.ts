export type ApplicationStatus = "Interested" | "Applied" | "Interview" | "Offer" | "Rejected";

export type Application = {
  id: number;
  company: string;
  initials: string;
  position: string;
  location: string;
  match: number;
  status: ApplicationStatus;
  applied: string;
  updated: string;
  nextStep: string;
  notes: string;
};

export const recentAnalyses = [
  { id: 1, role: "Junior AI Engineer", company: "Nimbus Labs", date: "Sep 14, 2026", match: 82, status: "Strong match" },
  { id: 2, role: "Machine Learning Engineer", company: "Arc Systems", date: "Sep 11, 2026", match: 71, status: "Good match" },
  { id: 3, role: "Data Analyst", company: "Northstar Data", date: "Sep 8, 2026", match: 68, status: "Good match" },
];

export const applications: Application[] = [
  { id: 1, company: "Nimbus Labs", initials: "NL", position: "Junior AI Engineer", location: "London, UK · Hybrid", match: 82, status: "Interview", applied: "Sep 10, 2026", updated: "Sep 14, 2026", nextStep: "Technical interview · Sep 18", notes: "Prepare to discuss the PV Visit Planner architecture and model evaluation choices." },
  { id: 2, company: "Arc Systems", initials: "AS", position: "Machine Learning Engineer", location: "Remote · Europe", match: 71, status: "Applied", applied: "Sep 8, 2026", updated: "Sep 8, 2026", nextStep: "Awaiting response", notes: "Application submitted with a tailored cover letter." },
  { id: 3, company: "Northstar Data", initials: "ND", position: "Data Analyst", location: "Nicosia, Cyprus", match: 68, status: "Interested", applied: "—", updated: "Sep 7, 2026", nextStep: "Tailor CV", notes: "Highlight Python analysis work and engineering background." },
  { id: 4, company: "Helio Energy", initials: "HE", position: "AI Solutions Associate", location: "Limassol, Cyprus", match: 76, status: "Offer", applied: "Aug 29, 2026", updated: "Sep 12, 2026", nextStep: "Respond by Sep 20", notes: "Review compensation and hybrid working terms." },
  { id: 5, company: "Vertex Works", initials: "VW", position: "Graduate Software Engineer", location: "Athens, Greece", match: 64, status: "Rejected", applied: "Aug 22, 2026", updated: "Sep 3, 2026", nextStep: "Closed", notes: "Keep for future graduate engineering openings." },
  { id: 6, company: "Lattice AI", initials: "LA", position: "AI Product Engineer", location: "Remote", match: 79, status: "Applied", applied: "Sep 2, 2026", updated: "Sep 9, 2026", nextStep: "Awaiting response", notes: "Strong product-building alignment. Docker remains a gap." },
];
