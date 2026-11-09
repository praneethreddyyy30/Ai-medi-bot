package com.medibot.model;

import jakarta.persistence.*;

/**
 * JPA Entity representing the clinical knowledge base of diseases.
 * Stored in the H2 / Relational database managed via Spring Data JPA.
 */
@Entity
@Table(name = "disease_knowledge_base")
public class DiseaseInfo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "disease_name", unique = true, nullable = false)
    private String diseaseName;

    @Column(name = "specialist_to_consult", nullable = false)
    private String specialistToConsult;

    @Column(name = "severity_level", nullable = false)
    private String severityLevel; // Low, Moderate, High, Emergency

    @Column(name = "home_remedies", length = 1000)
    private String homeRemedies;

    @Column(name = "precautions", length = 1000)
    private String precautions;

    public DiseaseInfo() {
    }

    public DiseaseInfo(String diseaseName, String specialistToConsult, String severityLevel, String homeRemedies, String precautions) {
        this.diseaseName = diseaseName;
        this.specialistToConsult = specialistToConsult;
        this.severityLevel = severityLevel;
        this.homeRemedies = homeRemedies;
        this.precautions = precautions;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getDiseaseName() {
        return diseaseName;
    }

    public void setDiseaseName(String diseaseName) {
        this.diseaseName = diseaseName;
    }

    public String getSpecialistToConsult() {
        return specialistToConsult;
    }

    public void setSpecialistToConsult(String specialistToConsult) {
        this.specialistToConsult = specialistToConsult;
    }

    public String getSeverityLevel() {
        return severityLevel;
    }

    public void setSeverityLevel(String severityLevel) {
        this.severityLevel = severityLevel;
    }

    public String getHomeRemedies() {
        return homeRemedies;
    }

    public void setHomeRemedies(String homeRemedies) {
        this.homeRemedies = homeRemedies;
    }

    public String getPrecautions() {
        return precautions;
    }

    public void setPrecautions(String precautions) {
        this.precautions = precautions;
    }
}
