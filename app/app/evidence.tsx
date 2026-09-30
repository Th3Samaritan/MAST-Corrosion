export function Evidence() {
  return (
    <article className="evidence-page">
      <section className="panel">
        <div className="eyebrow">SCIENTIFIC SCOPE</div>
        <h2>Measured rates. Conditional forecasts.</h2>
        <p>
          MAST estimates uniform metal loss from measurements. A position in an
          electrochemical series does not determine corrosion rate. Pitting,
          cracking and galvanic forward prediction require different evidence
          and models.
        </p>
        <p>
          No trained neural network or synthetic corrosion labels are used in
          these calculations. Field accuracy has not been established.
        </p>
      </section>
      <div className="method-grid">
        {[
          [
            'Thickness history',
            'A least-squares line uses every dated measurement at one inspection location. Rate is the negative slope. Tolerance bounds propagate the supplied absolute error through that slope; they exclude future operating changes.',
            'https://www.nasa.gov/wp-content/uploads/2023/06/nasa-rcmguide.pdf',
            'NASA maintenance guide',
          ],
          [
            'Corrosion current',
            'Faraday conversion: rate = 0.003272 × current density × equivalent weight / density. Units are µA/cm², g/equivalent and g/cm³, giving mm/year. Equivalent weight must match the dissolution chemistry.',
            'https://store.astm.org/standards/g102',
            'ASTM G102 scope',
          ],
          [
            'Polarization resistance',
            'Stern–Geary coefficient B = βaβc / [2.303(βa + βc)]. With slopes in mV/decade and Rp in Ω·cm², i = 1000B/Rp in µA/cm². Slopes must be established independently; passivation and transport effects can invalidate the estimate.',
            'https://help.gamry.com/Framework/experiments_c-dccorrosion.html',
            'Gamry calculation documentation',
          ],
          [
            'Coupon mass loss',
            'Rate = 87.6 × corrected mass loss / (density × area × exposure). Units are mg, g/cm³, cm² and hours. This gives an exposure-average rate; representativeness and cleaning correction require review.',
            'https://store.astm.org/standards/g31',
            'ASTM G31 scope',
          ],
        ].map(([title, text, url, label]) => (
          <section className="panel" key={title}>
            <h2>{title}</h2>
            <p>{text}</p>
            <a href={url} target="_blank" rel="noreferrer">
              {label} ↗
            </a>
          </section>
        ))}
      </div>
      <section className="panel">
        <h2>What the forecast means</h2>
        <p>
          Time to a user-supplied minimum equals the current thickness margin
          divided by a resolved positive rate. It assumes constant rate and
          exposure; it is neither safe service life nor an authorized inspection
          interval. Zero or negative loss does not prove safety.
        </p>
        <p>
          For current, LPR and coupon methods, the shaded range is a
          user-selected sensitivity. It is not a statistical confidence
          interval. A precise-looking decimal does not establish measurement
          precision.
        </p>
        <h2>Evidence and storage</h2>
        <p>
          Cloud snapshots are private to your Supabase account. The Render API
          validates inputs and recalculates results before saving. Saved records
          remain unreviewed; opening a record recalculates its inputs using the
          current engine. Device copies stay in the browser until removed.
          Export JSON for a portable copy.
        </p>
        <h2>Before a predictive AI release</h2>
        <p>
          Acquire representative experimental data, preserve units and
          provenance, hold out complete assets or studies, compare with physical
          baselines, test on independent sites and calibrate uncertainty. The
          existing synthetic dataset cannot validate field performance.
        </p>
        <a
          href="https://www.nist.gov/programs-projects/autonomous-scanning-droplet-cell"
          target="_blank"
          rel="noreferrer"
        >
          NIST physics-guided corrosion research ↗
        </a>
      </section>
    </article>
  );
}
