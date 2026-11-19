"""
https://claude.ai/chat/5346656d-0f3d-4888-9ee6-02cba853a4de

GaAs absorption edge: Lorentzian / Kramers-Kronig refinement of Urbach and gap fits.

Workflow
  0. Load E (eV) and transmittance T (from absorbance if needed).
  1. Estimate n in the transparent region from the transmission level. (This is where the bottom loss comes from?)
  2. First pass: alpha(E) with CONSTANT reflectance (your original analysis).
  3. Fit a Lorentzian edge oscillator (+ background dispersion) to ln(alpha),
     using only unsaturated data. The model is a complex epsilon(E), so n(E)
     comes out analytically and is automatically Kramers-Kronig consistent.
  4. Recompute R(E) from n(E), k(E), re-extract alpha, refit Urbach + gap.
  5. Iterate 3-4 until the gap stops changing; compare with the first pass.

With DATA_FILE = None the script runs on synthetic data so you can check it works.
"""
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

HC_EV_CM = 1.23984198e-4  # h*c in eV*cm

# ------------------------------- user settings -------------------------------
DATA_FILE = None              # e.g. "gaas.csv": columns energy_eV, absorbance (or T)
DATA_IS_ABSORBANCE = True     # True: column 2 is -log10(T); False: column 2 is T
THICKNESS_CM = 0.035          # wafer thickness d (350 um here)

E_TRANSPARENT = (1.20, 1.30)  # eV, below-gap range with negligible absorption
T_FLOOR = 3e-3                # T below this is treated as saturated -> masked
ALPHA_LORENTZ_RANGE = (1.0, 100.0)   # cm^-1, data used for the Lorentzian fit
ALPHA_URBACH_RANGE = (1.0, 100.0)    # cm^-1, data used for the Urbach fit
EG_INITIAL = 1.42             # eV, your earlier gap value (Lorentzian centre)
FIT_E0 = False                # let the Lorentzian centre float (strong correlations!)

USE_BG_OSCILLATOR = True      # background dispersion from high-energy transitions:
E0_BG = 3.55                  #   eps_bg = 1 + S/(E0_BG^2 - E^2)  (Wemple-DiDomenico-like;
                              #   check E0_BG against a reference). False -> constant eps_inf.
ALPHA_AT_GAP = 8000.0         # cm^-1, used only by the placeholder gap method below
MAX_ITER, TOL_EV = 10, 1e-6


# ------------------------------- optics helpers ------------------------------
def n_from_transparent_T(T):
    """Lossless slab, incoherent (fringes averaged): T = 2n/(n^2+1)."""
    return (1 + np.sqrt(1 - T**2)) / T


def reflectance(n, k):
    return ((n - 1)**2 + k**2) / ((n + 1)**2 + k**2)


def alpha_from_T(T, R, d):
    """Invert T = (1-R)^2 x / (1 - R^2 x^2), x = exp(-alpha d)."""
    T = np.clip(T, 1e-12, None)
    a, b = T * R**2, (1 - R)**2
    x = (-b + np.sqrt(b**2 + 4 * a * T)) / (2 * a)
    return -np.log(np.clip(x, 1e-300, None)) / d


def alpha_from_k(E, k):
    return 4 * np.pi * k * E / HC_EV_CM   # alpha = 4 pi k / lambda


# ------------------------------- dielectric model ----------------------------
def edge_term(E, A, E0, G):
    """Lorentz oscillator; imaginary part > 0 for absorption."""
    return A / (E0**2 - E**2 - 1j * G * E)


def eps_model(E, A, E0, G, n_ref, E_ref):
    """Edge oscillator + background, constrained so n(E_ref) = n_ref."""
    edge_ref = edge_term(E_ref, A, E0, G).real
    if USE_BG_OSCILLATOR:
        S = (n_ref**2 - 1 - edge_ref) * (E0_BG**2 - E_ref**2)
        bg = 1 + S / (E0_BG**2 - E**2)
    else:
        bg = n_ref**2 - edge_ref
    return bg + edge_term(E, A, E0, G)


def nk_model(E, A, E0, G, n_ref, E_ref):
    nt = np.sqrt(eps_model(E, A, E0, G, n_ref, E_ref).astype(complex))
    return nt.real, nt.imag


def lorentz_alpha(E, A, E0, G, n_ref, E_ref):
    return alpha_from_k(E, nk_model(E, A, E0, G, n_ref, E_ref)[1])


# ------------------------------- fits ----------------------------------------
def fit_lorentzian(E, alpha, Eg, n_ref, E_ref, p0):
    """Fit ln(alpha); parameters in log space (A, Gamma > 0)."""
    if FIT_E0:
        f = lambda E, lnA, lnG, E0: np.log(
            lorentz_alpha(E, np.exp(lnA), E0, np.exp(lnG), n_ref, E_ref))
        guess = list(p0[:2]) + [Eg]
    else:
        f = lambda E, lnA, lnG: np.log(
            lorentz_alpha(E, np.exp(lnA), Eg, np.exp(lnG), n_ref, E_ref))
        guess = list(p0[:2])
    popt, pcov = curve_fit(f, E, np.log(alpha), p0=guess, maxfev=20000)
    A, G = np.exp(popt[0]), np.exp(popt[1])
    E0 = popt[2] if FIT_E0 else Eg
    corr = pcov[0, 1] / np.sqrt(pcov[0, 0] * pcov[1, 1])
    return A, E0, G, popt, corr


def fit_urbach(E, alpha):
    """ln(alpha) = c + (E - 0)/E_U; returns slope, intercept, E_U, sigma(E_U)."""
    (slope, c), cov = np.polyfit(E, np.log(alpha), 1, cov=True)
    EU = 1 / slope
    return slope, c, EU, np.sqrt(cov[0, 0]) / slope**2


def determine_gap(E, alpha, slope, intercept):
    """PLACEHOLDER: replace with the method you used originally, so before/after
    comparisons are like-for-like. Here: energy where the Urbach line reaches
    ALPHA_AT_GAP (an extrapolation, sensitive to E_U)."""
    return (np.log(ALPHA_AT_GAP) - intercept) / slope


def select(E, alpha, T, rng, Emax=None):
    m = (T > T_FLOOR) & (alpha > rng[0]) & (alpha < rng[1]) & np.isfinite(alpha)
    if Emax is not None:
        m &= E < Emax
    return m


# ------------------------------- data ----------------------------------------
def synthetic_data(rng=np.random.default_rng(0)):
    """Urbach tail + above-gap absorption, dispersive n, stray-light floor, noise."""
    E = np.linspace(1.20, 1.55, 701)
    Eg, EU, ag = 1.424, 0.008, 8000.0
    alpha = np.where(E < Eg, ag * np.exp((E - Eg) / EU),
                     ag * (1 + 3 * np.sqrt(np.clip(E - Eg, 0, None))))
    n = np.sqrt(1 + 33.5 * 3.55 / (3.55**2 - E**2))
    n += 0.017 * (Eg**2 - E**2) * 0.06 / ((Eg**2 - E**2)**2 + (0.03 * E)**2)
    R = reflectance(n, 0)
    x = np.exp(-alpha * THICKNESS_CM)
    T = (1 - R)**2 * x / (1 - R**2 * x**2) + 5e-4 + rng.normal(0, 2e-4, E.size)
    return E, T


def load_data():
    if DATA_FILE is None:
        return synthetic_data()
    E, y = np.loadtxt(DATA_FILE, delimiter=",", unpack=True, skiprows=1)
    T = 10**(-y) if DATA_IS_ABSORBANCE else y
    order = np.argsort(E)
    return E[order], T[order]


# ------------------------------- main ----------------------------------------
def main():
    E, T = load_data()
    d = THICKNESS_CM

    # 1. n in the transparent region
    mt = (E > E_TRANSPARENT[0]) & (E < E_TRANSPARENT[1])
    n_ref, E_ref = n_from_transparent_T(np.mean(T[mt])), np.mean(E[mt])
    print(f"Transparent region: n = {n_ref:.4f} at E = {E_ref:.3f} eV")

    # 2. First pass: constant R
    R_const = reflectance(n_ref, 0)
    alpha0 = alpha_from_T(T, R_const, d)
    mu = select(E, alpha0, T, ALPHA_URBACH_RANGE, Emax=EG_INITIAL)
    s, c, EU0, dEU0 = fit_urbach(E[mu], alpha0[mu])
    Eg0 = determine_gap(E, alpha0, s, c)
    print(f"Pass 0 (const R={R_const:.4f}): E_U = {EU0*1e3:.3f} +/- {dEU0*1e3:.3f} meV,"
          f" Eg = {Eg0:.4f} eV")

    # 3-5. Iterate
    alpha, Eg, p = alpha0, Eg0, (np.log(0.01), np.log(0.02))
    for it in range(1, MAX_ITER + 1):
        ml = select(E, alpha, T, ALPHA_LORENTZ_RANGE)
        A, E0, G, popt, corr = fit_lorentzian(E[ml], alpha[ml], Eg, n_ref, E_ref, p)
        p = popt
        n_E, k_E = nk_model(E, A, E0, G, n_ref, E_ref)
        R_E = reflectance(n_E, k_E)
        alpha = alpha_from_T(T, R_E, d)
        mu = select(E, alpha, T, ALPHA_URBACH_RANGE, Emax=Eg)
        s, c, EU, dEU = fit_urbach(E[mu], alpha[mu])
        Eg_new = determine_gap(E, alpha, s, c)
        print(f"Iter {it}: A={A:.3e} eV^2, Gamma={G*1e3:.2f} meV, E0={E0:.4f} eV, "
              f"corr(lnA,lnG)={corr:+.3f} | E_U = {EU*1e3:.3f} +/- {dEU*1e3:.3f} meV,"
              f" Eg = {Eg_new:.4f} eV")
        done = abs(Eg_new - Eg) < TOL_EV
        Eg = Eg_new
        if done:
            break

    print(f"\nChange from refinement: dE_U = {(EU-EU0)*1e3:+.3f} meV, "
          f"dEg = {(Eg-Eg0)*1e3:+.3f} meV")

    # Plots
    fig, ax = plt.subplots(3, 1, figsize=(7, 10), sharex=True)
    ok0, ok = (T > T_FLOOR), (T > T_FLOOR)
    ax[0].semilogy(E[ok0], alpha0[ok0], ".", ms=2, label="alpha, constant R")
    ax[0].semilogy(E[ok], alpha[ok], ".", ms=2, label="alpha, R(E) from KK model")
    Ef = np.linspace(E.min(), Eg, 200)
    ax[0].semilogy(Ef, np.exp(c + s * Ef), "k--", label=f"Urbach, E_U={EU*1e3:.2f} meV")
    ax[0].semilogy(E, lorentz_alpha(E, A, E0, G, n_ref, E_ref), "r-", label="Lorentzian model")
    ax[0].set_ylim(0.1, 1e5); ax[0].set_ylabel("alpha (cm$^{-1}$)"); ax[0].legend(fontsize=8)
    ax[1].plot(E, n_E); ax[1].set_ylabel("n (model)")
    ax[2].plot(E, R_E, label="R(E)"); ax[2].axhline(R_const, ls=":", c="k", label="constant R")
    ax[2].set_ylabel("R"); ax[2].set_xlabel("Energy (eV)"); ax[2].legend(fontsize=8)
    for a in ax:
        a.axvline(Eg, c="gray", lw=0.8)
    fig.tight_layout(); fig.savefig("gaas_kk_refinement.png", dpi=150)
    print("Saved gaas_kk_refinement.png")


if __name__ == "__main__":
    main()