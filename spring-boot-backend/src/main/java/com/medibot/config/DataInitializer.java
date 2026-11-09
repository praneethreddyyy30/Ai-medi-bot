package com.medibot.config;

import com.medibot.model.DiseaseInfo;
import com.medibot.repository.DiseaseRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Seeds the H2 / SQL database with comprehensive clinical profiles for 45 diseases on startup.
 */
@Component
public class DataInitializer implements CommandLineRunner {

    private final DiseaseRepository diseaseRepository;

    public DataInitializer(DiseaseRepository diseaseRepository) {
        this.diseaseRepository = diseaseRepository;
    }

    @Override
    public void run(String... args) {
        if (diseaseRepository.count() > 0) {
            System.out.println("ℹ️ Disease knowledge base already initialized.");
            return;
        }

        List<DiseaseInfo> diseases = List.of(
            new DiseaseInfo("Common Cold", "General Physician", "Low",
                "Rest, stay hydrated with warm teas and water, use saline nasal spray or steam inhalation.",
                "Wash hands frequently, avoid close contact with others, avoid cold drafts."),

            new DiseaseInfo("Influenza", "General Physician", "Moderate",
                "Get bed rest, drink warm broths and fluids, use a humidifier, and take paracetamol if needed.",
                "Isolate during the fever period, wear a mask, monitor temperature closely."),

            new DiseaseInfo("COVID-19", "Pulmonologist / General Physician", "Moderate to High",
                "Rest, stay hydrated, monitor oxygen saturation (SpO2), practice breathing exercises.",
                "Strict isolation, wear N95 mask, seek emergency care if oxygen drops below 94%."),

            new DiseaseInfo("Dengue", "Infectious Disease Specialist", "High",
                "Drink plenty of fluids (water, ORS, tender coconut water) to maintain blood volume.",
                "Monitor platelet count daily, avoid aspirin or ibuprofen (risk of bleeding), rest strictly."),

            new DiseaseInfo("Malaria", "Infectious Disease Specialist", "High",
                "Rest in a cool environment, stay hydrated with electrolyte solutions.",
                "Seek immediate blood smear test, complete prescribed antimalarial course, use mosquito nets."),

            new DiseaseInfo("Typhoid Fever", "Infectious Disease Specialist", "High",
                "Drink boiled or bottled water, take ORS, eat soft digestible meals (khichdi, bananas, boiled potatoes).",
                "Maintain strict hand hygiene, finish full antibiotic course even after fever subsides."),

            new DiseaseInfo("Cholera", "Gastroenterologist / Emergency Care", "Emergency",
                "Administer large quantities of Oral Rehydration Salts (ORS) and electrolyte solutions immediately.",
                "Seek emergency IV fluid therapy, drink only boiled/purified water, wash hands thoroughly."),

            new DiseaseInfo("Chickenpox", "Dermatologist / General Physician", "Moderate",
                "Take cool oatmeal baths, apply calamine lotion, wear loose cotton clothing.",
                "Do not scratch blisters to prevent secondary bacterial infection and scarring, isolate until scabs form."),

            new DiseaseInfo("Measles", "Pediatrician / General Physician", "Moderate to High",
                "Rest in a dim room if eyes are sensitive to light, drink warm soothing fluids.",
                "Strict quarantine, monitor for respiratory complications, maintain good hydration."),

            new DiseaseInfo("Rubella", "General Physician", "Moderate",
                "Get plenty of bed rest, drink warm fluids, and maintain good hygiene.",
                "Isolate from pregnant women immediately (congenital rubella risk), monitor swollen glands."),

            new DiseaseInfo("Tetanus", "Emergency Medicine / Neurologist", "Emergency",
                "Clean any puncture wound immediately with soap and water.",
                "Immediate emergency hospital visit for tetanus toxoid and immunoglobulin, minimize light and noise stimulation."),

            new DiseaseInfo("Rabies", "Emergency Medicine Specialist", "Emergency",
                "Thoroughly wash animal bite wound with soap and running water for at least 15 minutes.",
                "Seek emergency post-exposure rabies vaccination (PEP) and rabies immunoglobulin immediately."),

            new DiseaseInfo("Hepatitis A", "Gastroenterologist / Hepatologist", "Moderate",
                "Rest well, eat a bland low-fat diet, drink plenty of fluids.",
                "Avoid alcohol completely, avoid acetaminophen overdose, practice strict sanitation."),

            new DiseaseInfo("Hepatitis B", "Hepatologist / Gastroenterologist", "High",
                "Adequate rest, nutritious balanced diet, stay well hydrated.",
                "Avoid alcohol, regular liver function monitoring, screen close contacts and vaccinate them."),

            new DiseaseInfo("Hepatitis C", "Hepatologist / Gastroenterologist", "High",
                "Rest, avoid alcohol and fatty foods, maintain good hydration.",
                "Consult for direct-acting antiviral therapy, do not share personal hygiene items (razors)."),

            new DiseaseInfo("Tuberculosis", "Pulmonologist / Chest Specialist", "High",
                "Eat high-protein nutritious meals, ensure well-ventilated living space, rest.",
                "Strict adherence to DOTS antibiotic therapy for full 6 months without skipping doses."),

            new DiseaseInfo("Dysentery", "Gastroenterologist", "Moderate to High",
                "Stay hydrated with ORS and electrolyte broths, follow the BRAT diet (bananas, rice, applesauce, toast).",
                "Drink only safe boiled water, wash hands before eating, seek stool test for amoebic vs bacterial."),

            new DiseaseInfo("Salmonella Infection", "Gastroenterologist", "Moderate",
                "Drink plenty of fluids, take oral rehydration salts, eat bland meals.",
                "Cook poultry and eggs thoroughly, avoid unpasteurized dairy, wash cutting boards."),

            new DiseaseInfo("Ebola", "Emergency Infectious Disease Team", "Emergency",
                "Immediate strict biocontainment isolation in an authorized medical facility.",
                "Do not touch body fluids, seek emergency specialized intensive care immediately."),

            new DiseaseInfo("Plague", "Infectious Disease Specialist", "Emergency",
                "Seek emergency medical hospitalization immediately for intravenous antibiotic treatment.",
                "Strict isolation, report to public health authorities, avoid contact with wild rodents."),

            new DiseaseInfo("Chikungunya", "Rheumatologist / General Physician", "Moderate to High",
                "Rest, maintain high fluid intake, apply cold compresses to painful swollen joints.",
                "Use paracetamol for pain, avoid aspirin, prevent mosquito bites using repellents."),

            new DiseaseInfo("Zika", "Infectious Disease Specialist", "Moderate",
                "Rest, drink plenty of fluids, take paracetamol for fever and pain.",
                "Pregnant women must consult doctor immediately due to microcephaly risk, use mosquito repellent."),

            new DiseaseInfo("SARS", "Pulmonologist / Critical Care", "Emergency",
                "Isolate in a hospital setting, monitor oxygen saturation continuously.",
                "Strict negative-pressure isolation, wear respiratory PPE, seek immediate intensive medical care."),

            new DiseaseInfo("MERS", "Pulmonologist / Critical Care", "Emergency",
                "Seek immediate hospitalization, isolate, and maintain hydration.",
                "Avoid contact with camels, practice strict respiratory hygiene, seek urgent ventilator support if needed."),

            new DiseaseInfo("West Nile Fever", "Neurologist / General Physician", "Moderate to High",
                "Get bed rest, stay hydrated, use over-the-counter pain relievers for headache.",
                "Monitor for severe neurological signs (confusion, stiff neck), prevent mosquito bites."),

            new DiseaseInfo("Yellow Fever", "Infectious Disease Specialist", "High to Emergency",
                "Rest in a cool room, drink electrolyte solutions, avoid NSAIDs and aspirin.",
                "Seek hospital care immediately, get yellow fever vaccine before travel to endemic zones."),

            new DiseaseInfo("Leptospirosis", "Infectious Disease Specialist", "High",
                "Stay hydrated, rest, and seek clinical diagnosis promptly.",
                "Avoid swimming or wading in floodwaters or water contaminated with animal urine."),

            new DiseaseInfo("Brucellosis", "Infectious Disease Specialist", "Moderate to High",
                "Rest, eat nutritious balanced food, stay hydrated.",
                "Complete full dual-antibiotic regimen, avoid raw/unpasteurized milk and dairy products."),

            new DiseaseInfo("Anthrax", "Emergency Medicine Specialist", "Emergency",
                "Seek emergency medical treatment immediately for urgent antibiotic therapy.",
                "Avoid contact with infected livestock, do not touch suspicious powders or spores."),

            new DiseaseInfo("Botulism", "Emergency Critical Care / Neurologist", "Emergency",
                "Seek emergency hospital treatment immediately for botulinum antitoxin administration.",
                "Do not consume bulging or improperly canned foods, seek immediate respiratory support if breathing is affected."),

            new DiseaseInfo("Meningitis", "Neurologist / Emergency Medicine", "Emergency",
                "Seek emergency hospitalization immediately; rest in a dark quiet room while awaiting ambulance.",
                "Watch for stiff neck, high fever, and sensitivity to light. Requires urgent lumbar puncture and IV antibiotics."),

            new DiseaseInfo("Encephalitis", "Neurologist / Critical Care", "Emergency",
                "Seek emergency hospital care immediately; ensure airway protection.",
                "Requires urgent brain imaging (MRI) and antiviral or antibacterial treatment."),

            new DiseaseInfo("Diphtheria", "Infectious Disease / ENT Specialist", "Emergency",
                "Seek emergency care for diphtheria antitoxin and antibiotic therapy.",
                "Strict respiratory isolation, monitor airway closely for pseudomembrane obstruction."),

            new DiseaseInfo("Whooping Cough", "Pulmonologist / Pediatrician", "Moderate to High",
                "Rest, stay well hydrated, use a cool mist humidifier, eat small frequent meals.",
                "Avoid irritants like smoke and dust, take prescribed macrolide antibiotics to reduce transmission."),

            new DiseaseInfo("Mumps", "Pediatrician / General Physician", "Moderate",
                "Apply warm or cold compresses to swollen salivary glands, eat soft foods, drink fluids.",
                "Isolate for 5 days after onset of swelling, avoid sour foods that stimulate salivary glands."),

            new DiseaseInfo("Polio", "Neurologist / Rehabilitation Specialist", "Emergency",
                "Seek emergency medical evaluation; complete bed rest is critical during active phase.",
                "Use warm moist packs for muscle spasms, ensure full vaccination series for community protection."),

            new DiseaseInfo("Typhus", "Infectious Disease Specialist", "High",
                "Rest, stay well hydrated, and seek prompt antibiotic treatment with doxycycline.",
                "Control body lice and flea exposure, wash clothing in hot water, maintain hygiene."),

            new DiseaseInfo("Rocky Mountain Spotted Fever", "Infectious Disease Specialist", "High to Emergency",
                "Seek immediate clinical evaluation for prompt doxycycline antibiotic therapy.",
                "Check for tick bites after outdoor activity, use DEET insect repellent, remove ticks carefully."),

            new DiseaseInfo("Lyme Disease", "Infectious Disease / Rheumatologist", "Moderate to High",
                "Rest, stay well hydrated, and follow full course of oral antibiotics.",
                "Monitor for expanding bulls-eye rash (erythema migrans), check skin for deer ticks after walking in wooded areas."),

            new DiseaseInfo("Leishmaniasis", "Dermatologist / Infectious Disease", "Moderate to High",
                "Keep sores clean and protected, maintain nutritious diet and fluid intake.",
                "Consult for antiparasitic treatment, use fine mesh bed nets and insect repellent against sandflies."),

            new DiseaseInfo("Schistosomiasis", "Gastroenterologist / Infectious Disease", "Moderate",
                "Stay hydrated and avoid contact with contaminated fresh water.",
                "Complete prescribed antiparasitic medication (praziquantel), avoid swimming in freshwater lakes in endemic areas."),

            new DiseaseInfo("Filariasis", "Infectious Disease / Vascular Specialist", "Moderate to High",
                "Keep affected limbs elevated, maintain strict local hygiene, exercise limb gently.",
                "Take prescribed antiparasitic medications, use mosquito nets to prevent re-infection."),

            new DiseaseInfo("Toxoplasmosis", "Infectious Disease Specialist", "Moderate",
                "Rest, eat well-cooked foods, stay hydrated.",
                "Pregnant women must avoid cleaning cat litter boxes, wash hands thoroughly after handling raw meat."),

            new DiseaseInfo("Cryptosporidiosis", "Gastroenterologist", "Moderate",
                "Stay hydrated with ORS, eat a bland diet, get adequate rest.",
                "Avoid swallowing swimming pool water, wash hands carefully, practice safe food handling.")
        );

        diseaseRepository.saveAll(diseases);
        System.out.println("✅ Successfully seeded " + diseases.size() + " disease clinical profiles into the database!");
    }
}
