import { useEffect, useState } from "react";
import "./App.css";

const API = "http://localhost:8000/api";

function App() {
  const [appliances, setAppliances] = useState([]);
  const [currentLoad, setCurrentLoad] = useState(0);
  const [remainingCapacity, setRemainingCapacity] = useState(800);

  const [name, setName] = useState("");
  const [wattage, setWattage] = useState("");
  const [priority, setPriority] = useState("");

  const loadAppliances = async () => {
    try {
      const response = await fetch(`${API}/appliances`);
      const data = await response.json();

      setAppliances(data.appliances);
      setCurrentLoad(data.current_load);
      setRemainingCapacity(data.remaining_capacity);
    } catch (error) {
      console.error("Failed to load appliances:", error);
    }
  };

  useEffect(() => {
    loadAppliances();
  }, []);

  const addAppliance = async (e) => {
    e.preventDefault();

    if (!name.trim() || !wattage || !priority) {
      alert("Please fill all fields");
      return;
    }

    if (Number(wattage) > 800) {
      alert("Wattage cannot exceed 800W");
      return;
    }

    try {
      const response = await fetch(`${API}/appliances`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: name.trim(),
          wattage: Number(wattage),
          priority: Number(priority),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Failed to add appliance");
        return;
      }

      setName("");
      setWattage("");
      setPriority("");

      loadAppliances();
    } catch (error) {
      alert("Backend is not running");
    }
  };

  const turnOn = async (id) => {
    try {
      const response = await fetch(`${API}/appliances/${id}/on`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Cannot turn on appliance");
        return;
      }

      loadAppliances();
    } catch (error) {
      alert("Something went wrong");
    }
  };

  const turnOff = async (id) => {
    try {
      const response = await fetch(`${API}/appliances/${id}/off`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Cannot turn off appliance");
        return;
      }

      loadAppliances();
    } catch (error) {
      alert("Something went wrong");
    }
  };

  const deleteAppliance = async (id) => {
    if (!window.confirm("Delete this appliance?")) {
      return;
    }

    try {
      const response = await fetch(`${API}/appliances/${id}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Cannot delete appliance");
        return;
      }

      loadAppliances();
    } catch (error) {
      alert("Something went wrong");
    }
  };

  return (
    <div className="app">
      <header>
        <h1>Inverter Load Manager</h1>
        <p>Manage your appliances within an 800W inverter capacity</p>
      </header>

      <main>
        <section className="dashboard">
          <div className="card">
            <span>Inverter Capacity</span>
            <strong>800W</strong>
          </div>

          <div className="card">
            <span>Current Load</span>
            <strong>{currentLoad}W</strong>
          </div>

          <div className="card">
            <span>Remaining Capacity</span>
            <strong>{remainingCapacity}W</strong>
          </div>
        </section>

        <section className="form-section">
          <h2>Add Appliance</h2>

          <form onSubmit={addAppliance}>
            <input
              type="text"
              placeholder="Appliance name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />

            <input
              type="number"
              placeholder="Wattage"
              min="1"
              value={wattage}
              onChange={(e) => setWattage(e.target.value)}
            />

            <input
              type="number"
              placeholder="Priority"
              min="1"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            />

            <button type="submit">Add Appliance</button>
          </form>

          <small>Lower priority number means higher importance.</small>
        </section>

        <section className="appliances">
          <div className="section-header">
            <h2>Appliances</h2>
            <button className="refresh" onClick={loadAppliances}>
              Refresh
            </button>
          </div>

          {appliances.length === 0 ? (
            <div className="empty">No appliances added yet.</div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Wattage</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {appliances.map((appliance) => (
                    <tr key={appliance.id}>
                      <td>{appliance.name}</td>

                      <td>{appliance.wattage}W</td>

                      <td>{appliance.priority}</td>

                      <td>
                        <span
                          className={`status ${appliance.state.toLowerCase()}`}
                        >
                          {appliance.state}
                        </span>
                      </td>

                      <td className="actions">
                        {appliance.state === "RUNNING" ? (
                          <button
                            className="off"
                            onClick={() => turnOff(appliance.id)}
                          >
                            Turn Off
                          </button>
                        ) : (
                          <button
                            className="on"
                            onClick={() => turnOn(appliance.id)}
                          >
                            Turn On
                          </button>
                        )}

                        <button
                          className="delete"
                          onClick={() => deleteAppliance(appliance.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="rules">
          <h2>System Rules</h2>

          <ul>
            <li>Maximum inverter capacity is 800W.</li>
            <li>Lower priority number means higher priority.</li>
            <li>Only lower-priority running appliances can be shed.</li>
            <li>
              Shed appliances can automatically restore when capacity is
              available.
            </li>
            <li>Explicitly turned OFF appliances never auto-restore.</li>
          </ul>
        </section>
      </main>
    </div>
  );
}

export default App;
